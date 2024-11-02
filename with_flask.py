import datetime
import logging
import threading
import time
from logging.handlers import RotatingFileHandler
from random import randint
from threading import Lock

from flask import Flask, jsonify, render_template_string
from opcua import Server
from waitress import serve

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
file_handler = RotatingFileHandler('opcua_server.log', maxBytes=1024 * 1024, backupCount=5)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
logger.addHandler(file_handler)

# Global variables with thread lock
sensor_lock = Lock()
sensor_values = {
    'machine1': {
        'temperature': {'current': 0, 'history': []},
        'pressure': {'current': 0, 'history': []}
    },
    'machine2': {
        'temperature': {'current': 0, 'history': []},
        'pressure': {'current': 0, 'history': []}
    },
    'last_update': None
}

# Maximum history points to keep
MAX_HISTORY_POINTS = 50

# Flask application
app = Flask(__name__)

# HTML template - will be in a separate artifact
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>OPC UA Sensor Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <nav class="bg-blue-600 text-white p-4 shadow-lg">
        <div class="container mx-auto">
            <h1 class="text-2xl font-bold">OPC UA Sensor Monitor</h1>
            <p class="text-sm">TENEZEU Assembly Line</p>
        </div>
    </nav>

    <div class="container mx-auto p-4">
        <div class="bg-white rounded-lg shadow-md p-4 mb-6">
            <div class="flex justify-between items-center">
                <h2 class="text-xl font-semibold text-gray-800">System Status</h2>
                <span id="connection-status" class="px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800">
                    Connected
                </span>
            </div>
            <p class="text-sm text-gray-600 mt-2">Last Update: <span id="last-update">--</span></p>
        </div>

        <div class="bg-white rounded-lg shadow-md p-4 mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">Machine 1</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="text-lg font-medium text-gray-700">Temperature</h3>
                        <span id="m1-temp" class="text-2xl font-bold text-blue-600">--°C</span>
                    </div>
                    <div class="chart-container">
                        <canvas id="m1-temp-chart"></canvas>
                    </div>
                </div>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="text-lg font-medium text-gray-700">Pressure</h3>
                        <span id="m1-press" class="text-2xl font-bold text-blue-600">-- hPa</span>
                    </div>
                    <div class="chart-container">
                        <canvas id="m1-press-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-lg shadow-md p-4">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">Machine 2</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="text-lg font-medium text-gray-700">Temperature</h3>
                        <span id="m2-temp" class="text-2xl font-bold text-blue-600">--°C</span>
                    </div>
                    <div class="chart-container">
                        <canvas id="m2-temp-chart"></canvas>
                    </div>
                </div>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="text-lg font-medium text-gray-700">Pressure</h3>
                        <span id="m2-press" class="text-2xl font-bold text-blue-600">-- hPa</span>
                    </div>
                    <div class="chart-container">
                        <canvas id="m2-press-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const chartConfig = {
            type: 'line',
            options: {
                animation: false,
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    },
                    x: {
                        display: false
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        };

        function createChart(elementId, color) {
            return new Chart(
                document.getElementById(elementId),
                {
                    ...chartConfig,
                    data: {
                        labels: [],
                        datasets: [{
                            data: [],
                            borderColor: color,
                            backgroundColor: color.replace(')', ', 0.1)'),
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true
                        }]
                    }
                }
            );
        }

        const charts = {
            m1Temp: createChart('m1-temp-chart', 'rgb(59, 130, 246)'),
            m1Press: createChart('m1-press-chart', 'rgb(16, 185, 129)'),
            m2Temp: createChart('m2-temp-chart', 'rgb(59, 130, 246)'),
            m2Press: createChart('m2-press-chart', 'rgb(16, 185, 129)')
        };

        function updateChart(chart, data) {
            chart.data.labels = data.map(h => new Date(h.timestamp).toLocaleTimeString());
            chart.data.datasets[0].data = data.map(h => h.value);
            chart.update();
        }

        async function fetchData() {
            try {
                const response = await fetch('/api/values');
                const data = await response.json();
                
                // Update charts
                updateChart(charts.m1Temp, data.machine1.temperature.history);
                updateChart(charts.m1Press, data.machine1.pressure.history);
                updateChart(charts.m2Temp, data.machine2.temperature.history);
                updateChart(charts.m2Press, data.machine2.pressure.history);
                
                // Update current values
                document.getElementById('m1-temp').textContent = `${data.machine1.temperature.current}°C`;
                document.getElementById('m1-press').textContent = `${data.machine1.pressure.current} hPa`;
                document.getElementById('m2-temp').textContent = `${data.machine2.temperature.current}°C`;
                document.getElementById('m2-press').textContent = `${data.machine2.pressure.current} hPa`;
                document.getElementById('last-update').textContent = new Date(data.last_update).toLocaleString();
                
                document.getElementById('connection-status').className = 'px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800';
                document.getElementById('connection-status').textContent = 'Connected';
            } catch (error) {
                console.error('Error fetching data:', error);
                document.getElementById('connection-status').className = 'px-3 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-800';
                document.getElementById('connection-status').textContent = 'Disconnected';
            }
        }

        // Update every second
        setInterval(fetchData, 1000);

        // Initial fetch
        fetchData();
    </script>
</body>
</html>
'''


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/values')
def get_values():
    with sensor_lock:
        current_values = {
            'machine1': {
                'temperature': {
                    'current': sensor_values['machine1']['temperature']['current'],
                    'history': list(sensor_values['machine1']['temperature']['history'][-MAX_HISTORY_POINTS:])
                },
                'pressure': {
                    'current': sensor_values['machine1']['pressure']['current'],
                    'history': list(sensor_values['machine1']['pressure']['history'][-MAX_HISTORY_POINTS:])
                }
            },
            'machine2': {
                'temperature': {
                    'current': sensor_values['machine2']['temperature']['current'],
                    'history': list(sensor_values['machine2']['temperature']['history'][-MAX_HISTORY_POINTS:])
                },
                'pressure': {
                    'current': sensor_values['machine2']['pressure']['current'],
                    'history': list(sensor_values['machine2']['pressure']['history'][-MAX_HISTORY_POINTS:])
                }
            },
            'last_update': datetime.datetime.now().isoformat()
        }
    return jsonify(current_values)


class OPCUAServer:
    def __init__(self):
        self.running = False
        self.server = None
        self._last_update = None

    def update_sensor_values(self, machine1_data, machine2_data):
        timestamp = datetime.datetime.now().isoformat()

        with sensor_lock:
            # Update Machine 1
            sensor_values['machine1']['temperature']['current'] = machine1_data['temperature']
            sensor_values['machine1']['pressure']['current'] = machine1_data['pressure']
            sensor_values['machine1']['temperature']['history'].append(
                {'value': machine1_data['temperature'], 'timestamp': timestamp}
            )
            sensor_values['machine1']['pressure']['history'].append(
                {'value': machine1_data['pressure'], 'timestamp': timestamp}
            )

            # Update Machine 2
            sensor_values['machine2']['temperature']['current'] = machine2_data['temperature']
            sensor_values['machine2']['pressure']['current'] = machine2_data['pressure']
            sensor_values['machine2']['temperature']['history'].append(
                {'value': machine2_data['temperature'], 'timestamp': timestamp}
            )
            sensor_values['machine2']['pressure']['history'].append(
                {'value': machine2_data['pressure'], 'timestamp': timestamp}
            )

            # Trim histories if needed
            for machine in ['machine1', 'machine2']:
                for sensor in ['temperature', 'pressure']:
                    if len(sensor_values[machine][sensor]['history']) > MAX_HISTORY_POINTS:
                        sensor_values[machine][sensor]['history'] = \
                            sensor_values[machine][sensor]['history'][-MAX_HISTORY_POINTS:]

            sensor_values['last_update'] = timestamp
            self._last_update = datetime.datetime.now()

    def setup_server(self):
        try:
            url = "opc.tcp://192.168.1.30:4840"  # Updated address
            self.server = Server()
            self.server.import_xml("model.xml")
            self.server.set_endpoint(url)

            # Register namespace
            uri = "http://yourorganisation.org/TENEZEU/"
            idx = self.server.register_namespace(uri)

            # Get Objects node
            objects = self.server.get_objects_node()

            # Create Assembly Line instance
            assembly_line = objects.add_object(idx, "AssemblyLine")

            # Create Machine 1
            machine1 = assembly_line.add_object(idx, "Machine1")
            sensor_temp1 = machine1.add_object(idx, "SensorTemp")
            self.temp1_unit = sensor_temp1.add_variable(idx, "Unite", "°C")
            self.temp1_value = sensor_temp1.add_variable(idx, "Valeur", 0.0)
            self.temp1_value.set_writable()

            sensor_press1 = machine1.add_object(idx, "SensorPression")
            self.press1_unit = sensor_press1.add_variable(idx, "Unite", "hPa")
            self.press1_value = sensor_press1.add_variable(idx, "Valeur", 0.0)
            self.press1_value.set_writable()

            # Create Machine 2
            machine2 = assembly_line.add_object(idx, "Machine2")
            sensor_temp2 = machine2.add_object(idx, "SensorTemp")
            self.temp2_unit = sensor_temp2.add_variable(idx, "Unite", "°C")
            self.temp2_value = sensor_temp2.add_variable(idx, "Valeur", 0.0)
            self.temp2_value.set_writable()

            sensor_press2 = machine2.add_object(idx, "SensorPression")
            self.press2_unit = sensor_press2.add_variable(idx, "Unite", "hPa")
            self.press2_value = sensor_press2.add_variable(idx, "Valeur", 0.0)
            self.press2_value.set_writable()

            logger.info(f"OPC UA Server setup completed successfully at {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to setup OPC UA server: {e}")
            return False

    def start(self):
        if not self.setup_server():
            return

        self.running = True
        self.server.start()
        logger.info("OPC UA Server started")

        while self.running:
            try:
                # Generate random values
                temp1 = randint(10, 50)
                temp2 = randint(10, 50)
                press1 = randint(200, 999)
                press2 = randint(200, 999)

                # Update OPC UA values
                self.temp1_value.set_value(float(temp1))
                self.temp2_value.set_value(float(temp2))
                self.press1_value.set_value(float(press1))
                self.press2_value.set_value(float(press2))

                # Update shared values thread-safely
                self.update_sensor_values(
                    {'temperature': temp1, 'pressure': press1},
                    {'temperature': temp2, 'pressure': press2}
                )

                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in OPC UA server loop: {e}")
                if not self.running:
                    break
                time.sleep(5)

        try:
            self.server.stop()
            logger.info("OPC UA Server stopped cleanly")
        except Exception as e:
            logger.error(f"Error stopping OPC UA server: {e}")


def run_server(opcua_server):
    try:
        opcua_server.start()
    except Exception as e:
        logger.error(f"Fatal error in OPC UA server: {e}")


if __name__ == '__main__':
    # Create and start OPC UA server in a separate thread
    opcua_server = OPCUAServer()
    opcua_thread = threading.Thread(target=run_server, args=(opcua_server,))
    opcua_thread.daemon = True
    opcua_thread.start()

    # Start Flask application with production server
    logger.info("Starting web server...")
    serve(app, host='0.0.0.0', port=5000)
