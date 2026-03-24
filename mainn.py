import network
import time
import json
from machine import Pin
from dht import DHT22
from umqtt.simple import MQTTClient

# ================= WiFi =================
SSID = "Wokwi-GUEST"
PASSWORD = ""

# ================= MQTT =================
BROKER = "test.mosquitto.org"
CLIENT_ID = "esp32-room"

# ================= Sensors =================
dht = DHT22(Pin(15))
pir = Pin(4, Pin.IN)

# ================= Connect WiFi =================
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

while not wifi.isconnected():
    time.sleep(1)

print("WiFi Connected")

# ================= Connect MQTT =================
client = MQTTClient(CLIENT_ID, BROKER)
client.connect()

print("MQTT Connected")

# ================= Main Loop =================
while True:
    dht.measure()

    temperature = dht.temperature()
    humidity = dht.humidity()
    occupancy = pir.value()

    payload = json.dumps({
        "room_id": "b01-f01-r001",
        "temperature": temperature,
        "humidity": humidity,
        "occupancy": bool(occupancy),
        "hvac_mode": "OFF"
    })

    topic = "campus/bldg_01/floor_01/room_001/telemetry"

    #  Send telemetry
    client.publish(topic, payload)

    #  Send heartbeat
    heartbeat_topic = topic.replace("telemetry", "heartbeat")
    client.publish(heartbeat_topic, '{"status": "alive"}')

    print("Sent:", payload)
    print("Heartbeat sent")

    time.sleep(5)