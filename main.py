import network
import time
import json
from machine import Pin, ADC
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

# Light sensor (LDR module AO → GPIO34)
light_sensor = ADC(Pin(34))
light_sensor.atten(ADC.ATTN_11DB)

# LED actuator
led = Pin(2, Pin.OUT)

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
    light_value = light_sensor.read()

    # ================= Smart Logic =================
    # Turn ON light only if someone is present AND it's dark
    if occupancy == 1 and light_value < 500:
        led.value(1)
        lighting_status = "ON"
    else:
        led.value(0)
        lighting_status = "OFF"

    # ================= Payload =================
    payload = json.dumps({
        "room_id": "b01-f01-r001",
        "temperature": temperature,
        "humidity": humidity,
        "occupancy": bool(occupancy),
        "light_level": light_value,
        "hvac_mode": "OFF",
        "lighting": lighting_status
    })

    topic = "campus/bldg_01/floor_01/room_001/telemetry"

    # ================= Send telemetry =================
    client.publish(topic, payload)

    # ================= Send heartbeat =================
    heartbeat_topic = topic.replace("telemetry", "heartbeat")
    client.publish(heartbeat_topic, '{"status": "alive"}')

    # ================= Debug =================
    print("Sent:", payload)
    print("Light:", light_value)
    print("LED:", lighting_status)
    print("Heartbeat sent\n")

    time.sleep(5)
