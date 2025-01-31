import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision

# MQTT configuration
MQTT_BROKER = "mqtt.example.com"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/#"
MQTT_CLIENT_ID = "mqtt_influx_subscriber"

# InfluxDB configuration
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "your-influxdb-token"
INFLUX_ORG = "your-org"
INFLUX_BUCKET = "your-bucket"

# Connect to InfluxDB
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=WritePrecision.NS)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Verbunden mit MQTT Broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Fehlgeschlagen mit Code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        print(f"Empfangen: {msg.topic} -> {payload}")
        
        # InfluxDB create point
        point = Point("sensors").tag("topic", msg.topic).field("value", float(payload))
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print("Daten in InfluxDB gespeichert")
    except Exception as e:
        print(f"Fehler: {e}")

# MQTT Client configuration
mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# start connection
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_forever()
