import serial
import struct
import time
import numpy as np


class LiteVNA:
    def __init__(self, port, baudrate=115200, timeout=1):
        """
        Initialize communication with LiteVNA.

        Args:
            port (str): Serial port (e.g., 'COM3' or '/dev/ttyUSB0').
            baudrate (int): Communication baud rate. Default is 115200.
            timeout (float): Timeout for serial communication in seconds.
        """
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)

    def close(self):
        """Close the serial port."""
        if self.ser.is_open:
            self.ser.close()

    def send_command(self, command):
        """Send a command to LiteVNA."""
        self.ser.write(command)

    def read_response(self, length):
        """Read the response from LiteVNA."""
        return self.ser.read(length)

    def write_register(self, address, value, length):
        """Write a value to a register."""
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
        """Read data from the values FIFO in chunks of up to 255 bytes."""
        data = b""
        while count > 0:
            chunk_size = min(count, 255)  # Read in chunks of at most 255 bytes
            command = struct.pack("B", 0x18) + struct.pack("B", address) + struct.pack("B", chunk_size)
            self.send_command(command)
            data += self.read_response(chunk_size)
            count -= chunk_size
        return data


    def clear_fifo(self, address):
        """Clear the FIFO by writing any value to it."""
        command = struct.pack("B", 0x20) + struct.pack("B", address) + struct.pack("B", 0x00)
        self.send_command(command)

    def configure_sweep(self, start_freq, step_freq, points):
        """Configure the sweep parameters."""
        # Set sweep start frequency (64-bit uint)
        self.write_register(0x00, start_freq, 8)
        # Set sweep step frequency (64-bit uint)
        self.write_register(0x10, step_freq, 8)
        # Set number of sweep points (16-bit uint)
        self.write_register(0x20, points, 2)

    def get_s11_magnitude(self, fifo_data):
        """
        Calculate S11 magnitude in dB from FIFO data.

        Args:
            fifo_data (bytes): 32-byte FIFO data.

        Returns:
            float: S11 magnitude in dB.
        """
        fwd0_re = int.from_bytes(fifo_data[0:4], "little", signed=True)
        fwd0_im = int.from_bytes(fifo_data[4:8], "little", signed=True)
        rev0_re = int.from_bytes(fifo_data[8:12], "little", signed=True)
        rev0_im = int.from_bytes(fifo_data[12:16], "little", signed=True)

        fwd0 = complex(fwd0_re, fwd0_im)
        rev0 = complex(rev0_re, rev0_im)

        # Normalize with forward wave (reference channel)
        s11 = rev0 / fwd0 if abs(fwd0) > 1e-9 else 0
        s11_magnitude_db = 20 * np.log10(abs(s11)) if abs(s11) > 1e-9 else -float("inf")
        return s11_magnitude_db


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

        print("Frequency (Hz), S11 Magnitude (dB)")

        while True:
            litevna.clear_fifo(0x30)  # Clear FIFO
            fifo_data = litevna.read_fifo(0x30, 32 * points)  # Read all points from FIFO

            for i in range(points):
                data = fifo_data[i * 32 : (i + 1) * 32]
                s11_magnitude_db = litevna.get_s11_magnitude(data)

                freq = start_freq + i * step_freq
                print(f"{freq}, {s11_magnitude_db}")

            time.sleep(0.1)  # Polling interval

    except KeyboardInterrupt:
        print("\nTerminating...")
    finally:
        litevna.close()


if __name__ == "__main__":
    main()
