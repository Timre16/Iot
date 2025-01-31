import serial
import struct
import numpy as np
import matplotlib.pyplot as plt

class LiteVNA:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self._initialize_calibration()

    def _initialize_calibration(self):
        """Sendet den Befehl, um kalibrierte Daten zu aktivieren."""
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
        self.write_register(0x00, start_freq, 8)  # sweepStartHz
        self.write_register(0x10, step_freq, 8)  # sweepStepHz
        self.write_register(0x20, points, 2)     # sweepPoints
        self.write_register(0x22, 1, 2)         # valuesPerFrequency = 1
        self.write_register(0x40, averages, 1)  # Average
        self.write_register(0x41, 0x01, 1)      # LowFrequencyPower
        self.write_register(0x42, 0x03, 1)      # HighFrequencyPower

    def get_s11_magnitude(self, fifo_data):
        fwd0_re = int.from_bytes(fifo_data[0:4], "little", signed=True)
        fwd0_im = int.from_bytes(fifo_data[4:8], "little", signed=True)
        rev0_re = int.from_bytes(fifo_data[8:12], "little", signed=True)
        rev0_im = int.from_bytes(fifo_data[12:16], "little", signed=True)

        fwd0 = complex(fwd0_re, fwd0_im)
        rev0 = complex(rev0_re, rev0_im)

        if abs(fwd0) > 1e-9:
            s11 = rev0 / fwd0
        else:
            s11 = 0

        s11_magnitude_db = 20 * np.log10(abs(s11)) if abs(s11) > 1e-9 else -float("inf")

        # Debugging-Ausgaben
        print(f"Debug - FWD: {fwd0}, REV: {rev0}, S11: {s11}, Magnitude: {s11_magnitude_db} dB")
        print(f"Raw FIFO Data: {fifo_data.hex()}")

        # Offset für Korrektur
        s11_magnitude_db += 2  # Falls nötig
        return s11_magnitude_db

def main():
    port = "COM3"  # Replace with your LiteVNA's port
    litevna = LiteVNA(port)

    try:
        start_freq = 1200000000  # 1.2 GHz
        stop_freq = 2000000000   # 2 GHz
        points = 201

        step_freq = (stop_freq - start_freq) // (points - 1)
        averages = 2
        litevna.configure_sweep(start_freq, step_freq, points, averages)

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

            if len(fifo_data) != 32 * points:
                print(f"Fehler: Erwartet {32 * points} Bytes, erhalten {len(fifo_data)} Bytes")
                continue

            s11_magnitudes = []
            for i in range(points):
                data = fifo_data[i * 32 : (i + 1) * 32]
                s11_magnitudes.append(litevna.get_s11_magnitude(data))

            # Update plot
            line.set_ydata(s11_magnitudes)
            ax.set_ylim(min(s11_magnitudes) - 1, max(s11_magnitudes) + 1)
            plt.pause(0.1)

    except KeyboardInterrupt:
        print("\nTerminating...")
    finally:
        litevna.close()

if __name__ == "__main__":
    main()
