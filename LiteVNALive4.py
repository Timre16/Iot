import serial
import struct
import cmath
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math

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

def update_polar_plot(frame, ser, scatter, magnitude_data, phase_data, num_values):
    try:
        send_command(ser, b'\x18\x30' + num_values.to_bytes(2, 'little'))
        raw_response = read_response(ser, expected_length=num_values * 32)

        magnitude_data.clear()
        phase_data.clear()

        for i in range(num_values):
            block = raw_response[i * 32:(i + 1) * 32]
            parsed_block = parse_fifo_block(block)

            fwd0 = complex(parsed_block["fwd0Re"], parsed_block["fwd0Im"])
            rev0 = complex(parsed_block["rev0Re"], parsed_block["rev0Im"])

            normalized = rev0 / fwd0
            magnitude = abs(normalized)
            phase = cmath.phase(normalized)

            magnitude_data.append(magnitude)
            phase_data.append(phase)

        scatter.set_offsets([(p, m) for p, m in zip(phase_data, magnitude_data)])
        return [scatter]

    except Exception as e:
        print(f"Error updating polar plot: {e}")
        return [scatter]

def main():
    SERIAL_PORT = "COM3"
    BAUD_RATE = 115200
    TIMEOUT = 1

    NUM_VALUES = 100

    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")

            fig = plt.figure(figsize=(8, 8))
            ax = plt.subplot(111, polar=True)

            magnitude_data = []
            phase_data = []

            scatter = ax.scatter([], [], s=10, label="S11 Parameter (Magnitude & Phase)")

            ax.set_ylim(0, 1.5)  # Adjust radial axis range if needed
            ax.set_xlabel("Phase (radians)")
            ax.set_ylabel("Magnitude")
            ax.grid(True)

            ani = animation.FuncAnimation(
                fig, update_polar_plot, fargs=(ser, scatter, magnitude_data, phase_data, NUM_VALUES), interval=1000, blit=True
            )

            plt.legend()
            plt.tight_layout()
            plt.show()

    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
