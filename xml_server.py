import time
from random import randint

from opcua import Server

# Configure and prepare the OPC Server
url = "opc.tcp://192.168.1.30:4840"
server = Server()

# Import the XML model
try:
    server.import_xml("model.xml")
    print("Information Model imported successfully from model.xml")
except Exception as e:
    print(f"Error importing model: {e}")
    exit(1)

server.set_endpoint(url)

# Register namespace
name = "OPCUA_RPI_TENEZEU"
uri = "http://yourorganisation.org/TENEZEU/"
idx = server.register_namespace(uri)

# Get Objects node
objects = server.get_objects_node()

# Create Assembly Line instance
assembly_line = objects.add_object(idx, "AssemblyLine")

# Create Machine 1
machine1 = assembly_line.add_object(idx, "Machine1")
# Machine 1 Sensors
sensor_temp1 = machine1.add_object(idx, "SensorTemp")
temp1_unit = sensor_temp1.add_variable(idx, "Unite", "°C")
temp1_value = sensor_temp1.add_variable(idx, "Valeur", 0.0)
temp1_value.set_writable()

sensor_press1 = machine1.add_object(idx, "SensorPression")
press1_unit = sensor_press1.add_variable(idx, "Unite", "hPa")
press1_value = sensor_press1.add_variable(idx, "Valeur", 0.0)
press1_value.set_writable()

# Create Machine 2
machine2 = assembly_line.add_object(idx, "Machine2")
# Machine 2 Sensors
sensor_temp2 = machine2.add_object(idx, "SensorTemp")
temp2_unit = sensor_temp2.add_variable(idx, "Unite", "°C")
temp2_value = sensor_temp2.add_variable(idx, "Valeur", 0.0)
temp2_value.set_writable()

sensor_press2 = machine2.add_object(idx, "SensorPression")
press2_unit = sensor_press2.add_variable(idx, "Unite", "hPa")
press2_value = sensor_press2.add_variable(idx, "Valeur", 0.0)
press2_value.set_writable()

# Start the server
server.start()
print(f"Server started at {url}")

try:
    while True:
        # Generate random values for all sensors
        temp1 = randint(10, 50)
        temp2 = randint(10, 50)
        press1 = randint(200, 999)
        press2 = randint(200, 999)

        # Update values
        temp1_value.set_value(float(temp1))
        temp2_value.set_value(float(temp2))
        press1_value.set_value(float(press1))
        press2_value.set_value(float(press2))

        # Print current values
        print(f"Machine 1 - Temperature: {temp1}°C, Pressure: {press1} hPa")
        print(f"Machine 2 - Temperature: {temp2}°C, Pressure: {press2} hPa")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping server...")
    server.stop()
    print("Server stopped")
except Exception as e:
    print(f"An error occurred: {e}")
    server.stop()
    print("Server stopped due to error")
