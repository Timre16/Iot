import paho.mqtt.client as mqtt
from datetime import datetime

# MQTT Konfiguration
MQTT_BROKER = "iot-lab01.ei.thm.de"
MQTT_PORT = 50313
MQTT_TOPIC = "THM/IoTLab/CCCEProjectMoisture/Data"

# MQTT-Client erstellen und verbinden
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Beispielhafte Daten senden
temperature = 22.5  # Beispielwert
zeit_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
client.publish(MQTT_TOPIC, str(temperature) + "; " + zeit_str)
print(f"Daten gesendet: {temperature} an {MQTT_TOPIC}")

# Verbindung schließen
client.disconnect()