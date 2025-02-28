import serial
import struct
import numpy as np
import matplotlib.pyplot as plt

class LiteVNA:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self._initialize_calibration()

    def _initialize_calibration(self):
        command = struct.pack("BBB", 0x20, 0x26, 0x03)
        self.send_command(command)
        print("Calibration mode enabled (0x20 0x26 0x03 sent).")

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

    def configure_sweep(self, start_freq, step_freq, points, averages=2):
        self.write_register(0x00, start_freq, 8)
        self.write_register(0x10, step_freq, 8)
        self.write_register(0x20, points, 2)
        self.write_register(0x22, 1, 2)
        self.write_register(0x40, averages, 1)
        self.write_register(0x41, 0x01, 1)
        self.write_register(0x42, 0x03, 1)

    def get_s11_complex(self, fifo_data):
        fwd0_re = int.from_bytes(fifo_data[0:4], "little", signed=True)
        fwd0_im = int.from_bytes(fifo_data[4:8], "little", signed=True)
        rev0_re = int.from_bytes(fifo_data[8:12], "little", signed=True)
        rev0_im = int.from_bytes(fifo_data[12:16], "little", signed=True)

        fwd0 = complex(fwd0_re, fwd0_im)
        rev0 = complex(rev0_re, rev0_im)

        if abs(fwd0) > 1e-9:
            return rev0 / fwd0
        else:
            return complex(0, 0)

def main():
    port = "COM3"  # Replace with your LiteVNA's port
    litevna = LiteVNA(port)

    try:
        start_freq = 1200000000  # 1.2 GHz
        stop_freq = 2000000000   # 2 GHz
        points = 201

        step_freq = (stop_freq - start_freq) // (points - 1)
        time_resolution = 1 / (stop_freq - start_freq) * points * 1e9  # Convert to nanoseconds
        time_series = np.linspace(0, time_resolution, points)

        averages = 2
        litevna.configure_sweep(start_freq, step_freq, points, averages)

        print("Initializing real-time time-domain plot...")
        plt.ion()
        fig, ax = plt.subplots()
        line, = ax.plot(time_series, np.zeros(points), label="Time-Domain Signal")
        ax.set_xlabel("Time (ns)")
        ax.set_ylabel("Amplitude")
        ax.set_title("Real-Time Time-Domain Signal")
        ax.legend()
        ax.grid()

        while True:
            litevna.clear_fifo(0x30)
            fifo_data = litevna.read_fifo(0x30, 32 * points)

            if len(fifo_data) != 32 * points:
                print(f"Error: Expected {32 * points} bytes, received {len(fifo_data)} bytes")
                continue

            s11_values = []
            for i in range(points):
                data = fifo_data[i * 32 : (i + 1) * 32]
                s11_values.append(litevna.get_s11_complex(data))

            # Convert Frequency Domain to Time Domain using IFFT
            time_signal = np.abs(np.fft.ifft(s11_values))
            time_signal = time_signal / np.max(time_signal) * 10  # Normalize and scale
            
            # Compute scaling range
            y_min = np.median(time_signal) - 2 * np.std(time_signal)
            y_max = np.median(time_signal) + 2 * np.std(time_signal)

            # Update plot
            line.set_ydata(time_signal)
            ax.set_ylim(y_min, y_max)
            plt.pause(0.1)

    except KeyboardInterrupt:
        print("\nTerminating...")
    finally:
        litevna.close()

if __name__ == "__main__":
    main()
