import serial
import time

def send_command(ser, command_bytes):
    """
    Sends a command to the LiteVNA and waits for a response.

    Args:
        ser (serial.Serial): The open serial connection.
        command_bytes (bytes): The command to send as bytes.
    """
    try:
        ser.write(command_bytes)
        print(f"Command sent: {command_bytes.hex()}")
    except Exception as e:
        print(f"Error sending command: {e}")

def read_response(ser, expected_length=1):
    """
    Reads the response from the LiteVNA.

    Args:
        ser (serial.Serial): The open serial connection.
        expected_length (int): The expected number of bytes in the response.

    Returns:
        bytes: The raw response data.
    """
    try:
        response = ser.read(expected_length)
        print(f"Response received: {response.hex()}")
        return response
    except Exception as e:
        print(f"Error reading response: {e}")
        return b''

def main():
    # Serial connection parameters
    SERIAL_PORT = "COM3"  # Replace with your serial port
    BAUD_RATE = 115200
    TIMEOUT = 1

    try:
        # Open the serial connection
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")

            # Example: Send an "INDICATE" command (0x0D)
            send_command(ser, b'\x0D')
            read_response(ser, expected_length=1)  # Expect 1-byte response ('2' or 0x32)

            # Example: Read the device variant register (0xF0)
            send_command(ser, b'\x10\xF0')  # READ command for address 0xF0
            read_response(ser, expected_length=1)  # Expect 1-byte response

            # Example: Read 10 values from the valuesFIFO (0x30)
            send_command(ser, b'\x18\x30\x0A')  # READFIFO for 10 values
            read_response(ser, expected_length=10 * 32)  # Expect 10 values, each 32 bytes

            print("Communication completed. Adjust commands as needed.")
    
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
