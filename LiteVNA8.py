import serial
import struct
import cmath
import csv
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math
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

def update_plot(frame, ser, line1, line2, magnitude_data_db, phase_data, ax):
    try:
        num_values = 100
        send_command(ser, b'\x18\x30' + num_values.to_bytes(2, 'little'))
        raw_response = read_response(ser, expected_length=num_values * 32)

        parsed_data = []
        for i in range(num_values):
            block = raw_response[i * 32:(i + 1) * 32]
            parsed_data.append(parse_fifo_block(block))

        magnitude_data_db.clear()
        phase_data.clear()

        for entry in parsed_data:
            fwd0 = complex(entry["fwd0Re"], entry["fwd0Im"])
            rev0 = complex(entry["rev0Re"], entry["rev0Im"])

            # Normalize rev0 with fwd0
            normalized = rev0 / fwd0

            # Convert to polar
            magnitude = abs(normalized)
            phase = cmath.phase(normalized)

            # Convert magnitude to dB
            magnitude_db = 20 * math.log10(magnitude) if magnitude > 0 else -float('inf')

            magnitude_data_db.append(magnitude_db)
            phase_data.append(phase)

        # Update plot data
        line1.set_ydata(magnitude_data_db)
        line2.set_ydata(phase_data)

        # Maintain consistent axis scaling
        ax.relim()
        ax.autoscale_view()

        return line1, line2

    except Exception as e:
        print(f"Error updating plot: {e}")
        return line1, line2

def main():
    # Serial connection parameters
    SERIAL_PORT = "COM3"  # Replace with your serial port
    BAUD_RATE = 115200
    TIMEOUT = 1

    try:
        # Open the serial connection
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")

            # Initialize plot
            fig, ax = plt.subplots(figsize=(10, 5))
            num_values = 100
            x_data = list(range(num_values))
            magnitude_data_db = [0] * num_values
            phase_data = [0] * num_values

            line1, = ax.plot(x_data, magnitude_data_db, label="Magnitude (dB)", color="blue")
            line2, = ax.plot(x_data, phase_data, label="Phase (radians)", color="orange")

            ax.set_title("Magnitude and Phase")
            ax.set_xlabel("Frequency Index")
            ax.set_ylabel("Value")
            ax.legend()
            ax.grid()

            # Set fixed axis limits
            ax.set_ylim(-30, 30)  # Adjust based on expected data ranges

            # Animate
            ani = animation.FuncAnimation(
                fig, update_plot, fargs=(ser, line1, line2, magnitude_data_db, phase_data, ax), interval=500, blit=True
            )

            plt.tight_layout()
            plt.show()

    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
