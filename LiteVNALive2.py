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

def update_plot(frame, ser, line_mag, line_phase, freq_data, magnitude_data_db, phase_data, num_values, start_freq, freq_step):
    try:
        magnitude_data_db.clear()
        phase_data.clear()

        for _ in range(1):  # Perform 8 measurements
            send_command(ser, b'\x18\x30' + num_values.to_bytes(2, 'little'))
            raw_response = read_response(ser, expected_length=num_values * 32)

            parsed_data = []
            for i in range(num_values):
                block = raw_response[i * 32:(i + 1) * 32]
                parsed_data.append(parse_fifo_block(block))

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

        # Update lines
        freq_data = [start_freq + i * freq_step for i in range(len(magnitude_data_db))]
        line_mag.set_data(freq_data, magnitude_data_db)
        line_phase.set_data(freq_data, phase_data)

        return [line_mag, line_phase]

    except Exception as e:
        print(f"Error updating plot: {e}")
        return [line_mag, line_phase]

def main():
    # Serial connection parameters
    SERIAL_PORT = "COM3"  # Replace with your serial port
    BAUD_RATE = 115200
    TIMEOUT = 1

    # Frequency parameters
    START_FREQ = 500e6  # 1.6 GHz
    FREQ_STEP = 1.8e6  # 1 MHz per step

    try:
        # Open the serial connection
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")

            # Initialize plot
            fig, ax = plt.subplots(figsize=(12, 6))
            num_values = 100

            magnitude_data_db = []
            phase_data = []
            freq_data = []

            line_mag, = ax.plot([], [], label="Magnitude (dB)", color="blue")
            line_phase, = ax.plot([], [], label="Phase (radians)", color="orange")

            ax.set_xlim(START_FREQ, START_FREQ + num_values * 1 * FREQ_STEP)
            ax.set_ylim(-100, 100)
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Magnitude (dB) / Phase (radians)")
            ax.legend()
            ax.grid()

            ani = animation.FuncAnimation(
                fig, update_plot, fargs=(ser, line_mag, line_phase, freq_data, magnitude_data_db, phase_data, num_values, START_FREQ, FREQ_STEP), interval=1000, blit=True
            )

            plt.tight_layout()
            plt.show()

    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
