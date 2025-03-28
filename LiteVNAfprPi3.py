import serial
import struct
import numpy as np
import paho.mqtt.client as mqtt
from datetime import datetime
import time

# MQTT Konfiguration
MQTT_BROKER = "localhost"
MQTT_PORT = 50233
MQTT_TOPIC = "THM/IoTLab/CCCEProjectMoisture/Data"

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
    port = "COM3"  # Replace with actual LiteVNA port
    litevna = LiteVNA(port)
    try:
        start_freq = 1200000000  # 1.2 GHz
        stop_freq = 2000000000   # 2 GHz
        points = 201
        step_freq = (stop_freq - start_freq) // (points - 1)
        averages = 2
        litevna.configure_sweep(start_freq, step_freq, points, averages)

        while True:
            litevna.clear_fifo(0x30)
            fifo_data = litevna.read_fifo(0x30, 32 * points)
            if len(fifo_data) != 32 * points:
                print(f"Fehler: Erwartet {32 * points} Bytes, erhalten {len(fifo_data)} Bytes")
                continue

            min_amplitude = float("inf")
            min_freq = None
            
            for i in range(0, 150, 1):
                data = fifo_data[i * 32: (i + 1) * 32]
                amplitude = litevna.get_s11_magnitude(data)
                freq = start_freq + i * step_freq
                if amplitude < min_amplitude:
                    min_amplitude = amplitude
                    min_freq = freq
            
            if min_freq is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"{timestamp};{min_freq / 1e9} GHz;{min_amplitude} dB"
                
                #client = mqtt.Client()
                #client.connect(MQTT_BROKER, MQTT_PORT, 60)
                #client.publish(MQTT_TOPIC, message)
                #client.disconnect()
                print(f"Daten gesendet: {message}")
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nTerminating...")
    finally:
        litevna.close()

if __name__ == "__main__":
    main()
