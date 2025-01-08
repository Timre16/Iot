import serial
import time

def display_vna_data(serial_port, baud_rate, timeout):
    """
    Reads data from a LiteVNA device via serial port and displays it in the command line.

    Args:
        serial_port (str): The name of the serial port (e.g., "COM3" or "/dev/ttyUSB0").
        baud_rate (int): The baud rate for serial communication (e.g., 115200).
        timeout (float): The timeout in seconds for reading from the serial port.
    """
    try:
        # Open the serial connection
        with serial.Serial(serial_port, baud_rate, timeout=timeout) as ser:
            print(f"Connected to {serial_port} at {baud_rate} baud.")
            
            # Example: Send initialization command (uncomment if needed)
            ser.write(bytes(b'\x10\x00'))
            time.sleep(3)  # Wait for the device to process the command
            
            last_data = None
            while True:
                try:
                    # Read a line of data from the serial port
                    line = ser.readline().decode('utf-8').strip()
                    if not line:
                        print("No data received.")
                        continue
                    
                    # Debugging: Print raw data
                    print(f"Raw data: {line}")
                    
                    # Parse the data (adjust based on LiteVNA output format)
                    data = line.split(',')
                    if len(data) == 3:  # Ensure it matches the expected format
                        last_data = data
                        print(f"Last Measured Data: Frequency = {data[0]} Hz, "
                              f"Magnitude = {data[1]} dB, Phase = {data[2]} deg")
                    else:
                        print(f"Unexpected data format: {line}")
                    
                    time.sleep(1)  # Wait for 1 second between updates
                except KeyboardInterrupt:
                    print("\nData display stopped by user.")
                    break
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # User-defined parameters
    SERIAL_PORT = "COM3"  # Change to your serial port
    BAUD_RATE = 115200    # Adjust according to the LiteVNA's specifications
    TIMEOUT = 1           # In seconds

    # Run the data display function
    display_vna_data(SERIAL_PORT, BAUD_RATE, TIMEOUT)
