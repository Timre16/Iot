import struct
import serial
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class LiteVNA:
    def __init__(self, port, baudrate=9600, timeout=1):
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)

    def send_command(self, command):
        self.ser.write(command)

    def read_response(self, length):
        return self.ser.read(length)

    def configure_sweep(self, start_freq, step_freq, points):
        # Configure sweep start frequency (8 bytes, uint64)
        self.send_command(struct.pack("B", 0x22) + struct.pack("<Q", start_freq) + b"\x00\x00\x00\x00")
        # Configure sweep step frequency (8 bytes, uint64)
        self.send_command(struct.pack("B", 0x22) + struct.pack("<Q", step_freq) + b"\x10\x00\x00\x00")
        # Configure number of points (2 bytes, uint16)
        self.send_command(struct.pack("B", 0x21) + struct.pack("<H", points) + b"\x20\x00")

    def clear_fifo(self, address):
        self.send_command(struct.pack("B", 0x20) + struct.pack("B", address) + b"\x01")

    def read_fifo(self, address, count):
        data = b""
        while count > 0:
            chunk_size = min(count, 255)  # Read in chunks of at most 255 bytes
            command = struct.pack("B", 0x18) + struct.pack("B", address) + struct.pack("B", chunk_size)
            self.send_command(command)
            data += self.read_response(chunk_size)
            count -= chunk_size
        return data

    def get_s11_magnitude(self, data):
        fwd0_re, fwd0_im, rev0_re, rev0_im = struct.unpack("<iiii", data[:16])
        ref_channel = complex(fwd0_re, fwd0_im)
        s11 = complex(rev0_re, rev0_im) / ref_channel
        magnitude_db = 20 * (s11.real ** 2 + s11.imag ** 2) ** 0.5
        return magnitude_db

    def close(self):
        self.ser.close()


def visualize(litevna, start_freq, step_freq, points):
    frequencies = [start_freq + i * step_freq for i in range(points)]
    s11_magnitudes = [0] * points

    fig, ax = plt.subplots()
    line, = ax.plot(frequencies, s11_magnitudes, label="S11 Magnitude (dB)")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("S11 Magnitude (dB)")
    ax.set_title("LiteVNA Real-Time Data")
    ax.legend()
    ax.grid()

    def update(frame):
        litevna.clear_fifo(0x30)
        fifo_data = litevna.read_fifo(0x30, 32 * points)

        for i in range(points):
            data = fifo_data[i * 32 : (i + 1) * 32]
            s11_magnitudes[i] = litevna.get_s11_magnitude(data)

        line.set_ydata(s11_magnitudes)
        return line,

    ani = FuncAnimation(fig, update, interval=200)
    plt.show()


def main():
    port = "COM3"  # Replace with your LiteVNA's port
    litevna = LiteVNA(port)

    try:
        # Configure sweep parameters
        start_freq = 1000000000  # 1 MHz
        stop_freq = 2000000000  # 30 MHz
        points = 801

        step_freq = (stop_freq - start_freq) // (points - 1)
        litevna.configure_sweep(start_freq, step_freq, points)

        # Visualize data
        visualize(litevna, start_freq, step_freq, points)

    except KeyboardInterrupt:
        print("\nTerminating...")
    finally:
        litevna.close()


if __name__ == "__main__":
    main()
