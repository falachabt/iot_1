import time

from opcua import Client

try:
    # Create client instance
    url = "opc.tcp://10.238.40.223:4840"  # 's IP address
    client = Client(url)

    # Connect to server
    client.connect()
    print("Client connected to:", url)

    # Get the root node
    objects = client.get_root_node()

    timestamp = client.get_node("ns=2;i=2")  # Numeric2 for Timestamp
    temperature = client.get_node("ns=2;i=3")  # Numeric3 for Temperature
    pressure = client.get_node("ns=2;i=4")  # Numeric4 for Pressure

    # Main loop to read values
    while True:
        try:
            # Read current values
            time_val = timestamp.get_value()
            temp_val = temperature.get_value()
            press_val = pressure.get_value()

            # Print the values
            print(f"Timestamp: {time_val}")
            print(f"Temperature: {temp_val}°C")
            print(f"Pressure: {press_val} hPa")
            print("-" * 50)

            # Wait for 1 second before next reading
            time.sleep(1)

        except Exception as e:
            print(f"Error reading values: {e}")
            time.sleep(1)
            continue

except Exception as e:
    print(f"Connection failed: {e}")

finally:
    # Ensure client disconnects properly
    try:
        client.disconnect()
        print("Client disconnected")
    except:
        pass
