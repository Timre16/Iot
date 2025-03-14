import paho.mqtt.client as mqtt
import time
import random

# MQTT Configuration
MQTT_BROKER = "iot-lab-03.ei.thm.de"
MQTT_PORT = 50313
MQTT_TOPIC = "THM/IoTLab/CCCEProjectMoisture/Data"

# Create and connect MQTT client
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

try:
    while True:
        # Generate a random moisture value (adjust range as needed)
        moisture_value = round(random.uniform(0, 100), 6)  # Random value between 0 and 100

        # Publish the value
        client.publish(MQTT_TOPIC, str(moisture_value))
        print(f"Sent moisture value: {moisture_value} to {MQTT_TOPIC}")

        # Wait for 5 seconds before sending the next value
        time.sleep(5)

except KeyboardInterrupt:
    print("Stopping MQTT publisher...")

finally:
    client.disconnect()
