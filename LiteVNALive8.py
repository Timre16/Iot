import serial
import struct
import time
import numpy as np
import matplotlib.pyplot as plt


class LiteVNA:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)

    def close(self):
        if self.ser.is_open:
            self.ser.close()

    def send_command(self, command):
        self.ser.write(command)

    def read_response(self, length):
        return self.ser.read(length)

    def write_register(self, address, value, length):
        if length == 1:
            command = struct.pack("B", 0x20) + struct.pack("B", address) + struct.pack("B", value)
        elif length == 2:
            command = struct.pack("B", 0x21) + struct.pack("B", address) + struct.pack("<H", value)
        elif length == 4:
            command = struct.pack("B", 0x22) + struct.pack("B", address) + struct.pack("<I", value)
        elif length == 8:
            command = struct.pack("B", 0x23) + struct.pack("B", address) + value.to_bytes(8, "little")
        else:
            raise ValueError("Unsupported register length.")
        self.send_command(command)

    def read_fifo(self, address, count):
        data = b""
        while count > 0:
            chunk_size = min(count, 255)
            command = struct.pack("B", 0x18) + struct.pack("B", address) + struct.pack("B", chunk_size)
            self.send_command(command)
            data += self.read_response(chunk_size)
            count -= chunk_size
        return data

    def clear_fifo(self, address):
        command = struct.pack("B", 0x20) + struct.pack("B", address) + struct.pack("B", 0x00)
        self.send_command(command)

    def configure_sweep(self, start_freq, step_freq, points):
        self.write_register(0x00, start_freq, 8)
        self.write_register(0x10, step_freq, 8)
        self.write_register(0x20, points, 2)

    def get_s11_magnitude(self, fifo_data):
        fwd0_re = int.from_bytes(fifo_data[0:4], "little", signed=True)
        fwd0_im = int.from_bytes(fifo_data[4:8], "little", signed=True)
        rev0_re = int.from_bytes(fifo_data[8:12], "little", signed=True)
        rev0_im = int.from_bytes(fifo_data[12:16], "little", signed=True)

        fwd0 = complex(fwd0_re, fwd0_im)
        rev0 = complex(rev0_re, rev0_im)

        s11 = rev0 / fwd0 if abs(fwd0) > 1e-9 else 0
        s11_magnitude_db = 20 * np.log10(abs(s11)) if abs(s11) > 1e-9 else -float("inf")
        return s11_magnitude_db


def main():
    port = "COM3"  # Replace with your LiteVNA's port
    litevna = LiteVNA(port)

    try:
        start_freq = 1000000000  # 1 GHz
        stop_freq = 2000000000  # 2 GHz
        points = 801

        step_freq = (stop_freq - start_freq) // (points - 1)
        litevna.configure_sweep(start_freq, step_freq, points)

        print("Initializing real-time plot...")
        plt.ion()
        fig, ax = plt.subplots()
        freqs = np.linspace(start_freq, stop_freq, points)
        line, = ax.plot(freqs, np.zeros(points), label="S11 Magnitude (dB)")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("S11 Magnitude (dB)")
        ax.set_title("Real-Time S11 Magnitude")
        ax.legend()
        ax.grid()

        while True:
            litevna.clear_fifo(0x30)
            fifo_data = litevna.read_fifo(0x30, 32 * points)

            s11_magnitudes = []
            for i in range(points):
                data = fifo_data[i * 32 : (i + 1) * 32]
                s11_magnitudes.append(litevna.get_s11_magnitude(data))

            # Update plot
            line.set_ydata(s11_magnitudes)
            ax.set_ylim(min(s11_magnitudes) - 1, max(s11_magnitudes) + 1)  # Adjust y-axis dynamically
            plt.pause(0.1)

    except KeyboardInterrupt:
        print("\nTerminating...")
    finally:
        litevna.close()


if __name__ == "__main__":
    main()
