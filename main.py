import datetime
import time
from random import randint

from opcua import ua, Server

# Configure and prepare the OPC Server
url = "opc.tcp://10.238.42.132:4840"  # Enter the RPI IP address on port 4840
server = Server()
server.set_endpoint(url)

print("every thing oky here ")

name = "OPCUA_RPI_SERVER_GroupeX"  # Enter your group number here
addspace = server.register_namespace(name)
node = server.get_objects_node()

param = node.add_object(addspace, "Parameters")
timestamp = param.add_variable(addspace, "Timestamp", ua.Variant(0, ua.VariantType.DateTime))
temperature = param.add_variable(addspace, "Temperature", ua.Variant(0, ua.VariantType.Double))
pression = param.add_variable(addspace, "Pressure", ua.Variant(0, ua.VariantType.Double))

# Set variables to be writable by clients
timestamp.set_writable()
temperature.set_writable()
pression.set_writable()

# Start the Server
server.start()
print("Server started a t {}".format(url))

try:
    while True:
        current_time = datetime.datetime.now()
        temp_value = randint(10, 50)
        press_value = randint(200, 999)

        # Update the values
        timestamp.set_value(current_time)
        temperature.set_value(temp_value)
        pression.set_value(press_value)

        print(f"Time: {current_time}, Temperature: {temp_value}°C, Pressure: {press_value} hPa")
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopping server...")
    server.stop()
