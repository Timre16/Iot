import serial
import time

def log_raw_data(serial_port, baud_rate, timeout, log_file):
    """
    Logs raw data from a LiteVNA device to a file for debugging.

    Args:
        serial_port (str): The name of the serial port (e.g., "COM3" or "/dev/ttyUSB0").
        baud_rate (int): The baud rate for serial communication (e.g., 115200).
        timeout (float): The timeout in seconds for reading from the serial port.
        log_file (str): The name of the file to save the raw data.
    """
    try:
        # Open the serial connection
        with serial.Serial(serial_port, baud_rate, timeout=timeout) as ser, open(log_file, 'w') as file:
            print(f"Connected to {serial_port} at {baud_rate} baud.")
            print(f"Logging raw data to {log_file}...")

            ser.write(bytes(b'\x18\30\10\r'))
            time.sleep(3)  # Wait for the device to process the command
            
            while True:
                try:
                    # Read raw data from the serial port
                    line = ser.readline()
                    print(f"Raw bytes: {line}")  # Debug raw byte output
                    
                    # Save raw data to the file
                    file.write(f"{line}\n")
                    file.flush()  # Ensure the data is written to disk
                    
                    time.sleep(1)  # Pause for 1 second between reads
                except KeyboardInterrupt:
                    print("\nLogging stopped by user.")
                    break
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # User-defined parameters
    SERIAL_PORT = "COM3"         # Change to your serial port
    BAUD_RATE = 115200           # Adjust according to the LiteVNA's specifications
    TIMEOUT = 1                  # In seconds
    LOG_FILE = "litevna_raw_data.log"  # File to save the raw data

    # Start logging raw data
    log_raw_data(SERIAL_PORT, BAUD_RATE, TIMEOUT, LOG_FILE)
