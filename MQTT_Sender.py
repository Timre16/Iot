import paho.mqtt.client as mqtt

# MQTT Konfiguration
MQTT_BROKER = "mqtt.ei.thm.de"
MQTT_PORT = 1993
MQTT_TOPIC = "THM/IoTLab/CCCEProjectMoisture/Data"

# MQTT-Client erstellen und verbinden
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Beispielhafte Daten senden
temperature = 22.5  # Beispielwert
client.publish(MQTT_TOPIC, temperature)
print(f"Daten gesendet: {temperature} an {MQTT_TOPIC}")

# Verbindung schließen
client.disconnect()