import serial
import struct
import cmath
import csv

number_of_values = 100

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


def parse_fifo_block(block):
    """
    Parses a 32-byte FIFO block from the LiteVNA.

    Args:
        block (bytes): A 32-byte data block from the valuesFIFO.

    Returns:
        dict: Parsed data fields as a dictionary.
    """
    if len(block) != 32:
        raise ValueError("Block size must be 32 bytes.")

    data = {
        "fwd0Re": struct.unpack('<i', block[0:4])[0],
        "fwd0Im": struct.unpack('<i', block[4:8])[0],
        "rev0Re": struct.unpack('<i', block[8:12])[0],
        "rev0Im": struct.unpack('<i', block[12:16])[0],
        "rev1Re": struct.unpack('<i', block[16:20])[0],
        "rev1Im": struct.unpack('<i', block[20:24])[0],
        "freqIndex": struct.unpack('<H', block[24:26])[0],
    }

    return data


def main():
    # Serial connection parameters
    SERIAL_PORT = "COM3"  # Replace with your serial port
    BAUD_RATE = 115200
    TIMEOUT = 1

    try:
        # Open the serial connection
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")

            # Example: Read 10 values from the valuesFIFO (0x30)
            send_command(ser, b'\x18\x30\x64')  # READFIFO for 10 values
            raw_response = read_response(ser, expected_length=number_of_values * 32)  # Expect 10 values, each 32 bytes

            # Parse the response
            parsed_data = []
            for i in range(number_of_values):
                block = raw_response[i * 32:(i + 1) * 32]
                parsed_data.append(parse_fifo_block(block))

            # Prepare CSV output
            csv_filename = "C:/Users/timei/Desktop/litevna_data.csv"
            with open(csv_filename, mode="w", newline="") as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=';')

                # Write header
                header = []
                header.append(f"Magnitude")
                header.append(f"Phase (radians)")
                csv_writer.writerow(header)

                # Write data
                for entry in parsed_data:
                    fwd0 = complex(entry["fwd0Re"], entry["fwd0Im"])
                    rev0 = complex(entry["rev0Re"], entry["rev0Im"])

                    # Normalize rev0 with fwd0
                    normalized = rev0 / fwd0

                    # Convert to polar
                    magnitude = abs(normalized)
                    phase = cmath.phase(normalized)

                    csv_writer.writerow([magnitude, phase])

            print(f"Data saved to {csv_filename}")

    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
