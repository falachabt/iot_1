import random
import time
from datetime import datetime

from opcua import Client


def write_values(temperature_node, pressure_node, timestamp_node):
    """Function to write new values to the server"""
    try:
        # Generate new values
        new_temp = random.uniform(15, 35)  # Random temperature between 15-35°C
        new_pressure = random.uniform(980, 1020)  # Random pressure between 980-1020 hPa
        current_time = datetime.now()

        # Write new values to the server
        temperature_node.set_value(new_temp)
        pressure_node.set_value(new_pressure)
        timestamp_node.set_value(current_time)

        print(f"\nSuccessfully wrote new values:")
        print(f"New Temperature: {new_temp:.1f}°C")
        print(f"New Pressure: {new_pressure:.1f} hPa")
        print(f"New Timestamp: {current_time}")
        return True

    except Exception as e:
        print(f"Error writing values: {e}")
        return False


try:
    # Create client instance
    url = "opc.tcp://192.168.1.45:4840"
    client = Client(url)

    # Connect to server
    client.connect()
    print("Client connected to:", url)

    # Get the nodes using the numeric identifiers
    timestamp = client.get_node("ns=2;i=2")  # Numeric2 for Timestamp
    temperature = client.get_node("ns=2;i=3")  # Numeric3 for Temperature
    pressure = client.get_node("ns=2;i=4")  # Numeric4 for Pressure

    while True:
        try:
            # Read current values
            time_val = timestamp.get_value()
            temp_val = temperature.get_value()
            press_val = pressure.get_value()

            # Print current values
            print("\nCurrent Values:")
            print(f"Timestamp: {time_val}")
            print(f"Temperature: {temp_val}°C")
            print(f"Pressure: {press_val} hPa")
            print("-" * 50)

            # Ask user if they want to write new values
            user_input = input("\nDo you want to write new values? (y/n): ").lower()

            if user_input == 'y':
                # Option menu for writing values
                print("\nSelect an option:")
                print("1. Write random values")
                print("2. Enter custom values")
                print("3. Continue monitoring")

                option = input("Enter your choice (1-3): ")

                if option == '1':
                    write_values(temperature, pressure, timestamp)

                elif option == '2':
                    try:
                        # Get custom values from user
                        new_temp = float(input("Enter new temperature (°C): "))
                        new_pressure = float(input("Enter new pressure (hPa): "))

                        # Write custom values
                        temperature.set_value(new_temp)
                        pressure.set_value(new_pressure)
                        timestamp.set_value(datetime.now())

                        print("\nSuccessfully wrote custom values!")
                    except ValueError:
                        print("Invalid input! Please enter numeric values.")

                print("\nContinuing monitoring...")

            # Wait before next reading
            time.sleep(1)

        except Exception as e:
            print(f"Error in operation: {e}")
            time.sleep(1)
            continue

except Exception as e:
    print(f"Connection failed: {e}")

finally:
    try:
        client.disconnect()
        print("Client disconnected")
    except:
        pass
