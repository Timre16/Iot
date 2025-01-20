import serial
import struct
import cmath
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def send_command(ser, command_bytes):
    try:
        ser.write(command_bytes)
        print(f"Command sent: {command_bytes.hex()}")
    except Exception as e:
        print(f"Error sending command: {e}")

def read_response(ser, expected_length=1):
    try:
        response = ser.read(expected_length)
        print(f"Response received: {response.hex()}")
        return response
    except Exception as e:
        print(f"Error reading response: {e}")
        return b''

def parse_fifo_block(block):
    if len(block) != 32:
        raise ValueError("Block size must be 32 bytes.")

    data = {
        "fwd0Re": struct.unpack('<i', block[0:4])[0],
        "fwd0Im": struct.unpack('<i', block[4:8])[0],
        "rev0Re": struct.unpack('<i', block[8:12])[0],
        "rev0Im": struct.unpack('<i', block[12:16])[0],
        "freqIndex": struct.unpack('<H', block[24:26])[0],
    }
    return data

def update_plot(frame, ser, line, freq_data, magnitude_data_db, num_values, start_freq, freq_step):
    try:
        magnitude_data_db.clear()
        freq_data.clear()

        send_command(ser, b'\x18\x30' + num_values.to_bytes(2, 'little'))
        raw_response = read_response(ser, expected_length=num_values * 32)

        for i in range(num_values):
            block = raw_response[i * 32:(i + 1) * 32]
            parsed_block = parse_fifo_block(block)

            fwd0 = complex(parsed_block["fwd0Re"], parsed_block["fwd0Im"])
            rev0 = complex(parsed_block["rev0Re"], parsed_block["rev0Im"])

            if abs(fwd0) > 0:
                normalized = rev0 / fwd0

                # Calculate magnitude in dB and negate it
                magnitude = abs(normalized)
                magnitude_db = -20 * math.log10(magnitude) if magnitude > 0 else -float('inf')  # Negate the value
                magnitude_data_db.append(magnitude_db)
            else:
                magnitude_data_db.append(-float('inf'))  # Handle division by zero

            # Calculate corresponding frequency
            freq = start_freq + parsed_block["freqIndex"] * freq_step
            freq_data.append(freq)

        line.set_data(freq_data, magnitude_data_db)
        plt.gca().relim()
        plt.gca().autoscale_view()
        return [line]

    except Exception as e:
        print(f"Error updating plot: {e}")
        return [line]


def main():
    SERIAL_PORT = "COM3"  # Replace with your serial port
    BAUD_RATE = 115200
    TIMEOUT = 1

    START_FREQ = 1.2e9  # Start at 1.2 GHz
    END_FREQ = 2e9      # End at 2 GHz
    FREQ_STEP = (END_FREQ - START_FREQ) / 100  # Divide into 100 points
    NUM_VALUES = 100  # Number of frequency points

    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")

            # Set up the plot
            fig, ax = plt.subplots(figsize=(10, 6))
            freq_data = []
            magnitude_data_db = []

            line, = ax.plot([], [], label="S11 Magnitude (dB)", color="blue")
            ax.set_xlim(START_FREQ, END_FREQ)
            ax.set_ylim(-5, 5)  # Typical range for dB magnitude
            ax.set_xlabel("Frequency (GHz)")
            ax.set_ylabel("Magnitude (dB)")
            ax.grid()
            ax.legend()

            ani = animation.FuncAnimation(
                fig, update_plot, fargs=(ser, line, freq_data, magnitude_data_db, NUM_VALUES, START_FREQ, FREQ_STEP),
                interval=1000, blit=True
            )

            plt.tight_layout()
            plt.show()

    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
