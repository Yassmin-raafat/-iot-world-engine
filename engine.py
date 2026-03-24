import asyncio
import random
import json
from gmqtt import Client as MQTTClient
import sqlite3
import time

BROKER = "test.mosquitto.org"

# ================= CONFIG =================
CONFIG = {
    "num_floors": 4,
    "rooms_per_floor":5,
    "light_threshold": 1500
}

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("rooms.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        room_id TEXT PRIMARY KEY,
        temperature REAL,
        humidity REAL,
        hvac_mode TEXT,
        last_update INTEGER
    )
    """)

    conn.commit()
    conn.close()


def save_room(room):
    conn = sqlite3.connect("rooms.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO rooms (room_id, temperature, humidity, hvac_mode, last_update)
    VALUES (?, ?, ?, ?, ?)
    """, (
        room.room_id,
        room.temperature,
        room.humidity,
        room.hvac_mode,
        int(time.time())
    ))

    conn.commit()
    conn.close()


def load_rooms():
    conn = sqlite3.connect("rooms.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM rooms")
    rows = cursor.fetchall()

    conn.close()
    return rows


# ================= ROOM =================
class Room:
    def __init__(self, building_id, floor_id, room_id):
        self.building_id = building_id
        self.floor_id = floor_id
        self.room_id = room_id

        self.temperature = 22.0
        self.humidity = 50.0
        self.occupancy = False
        self.hvac_mode = "OFF"
        self.light_level = 1000
        self.lighting = "OFF"

    def update(self):
        # Drift Compensation
        self.temperature += random.uniform(-0.2, 0.2)
        self.humidity += random.uniform(-0.5, 0.5)
        self.light_level += random.randint(-50, 50)

        # Fault Modeling
        if random.random() < 0.05:
            self.temperature = None

        # Occupancy
        self.occupancy = random.choice([True, False])

        # Smart lighting logic
        if self.occupancy and self.light_level < CONFIG["light_threshold"]:
            self.lighting = "ON"
        else:
            self.lighting = "OFF"

    def get_topic(self):
        return f"campus/bldg_01/floor_{self.floor_id:02d}/room_{self.room_id[-3:]}/telemetry"

    def to_json(self):
        return json.dumps({
            "room_id": self.room_id,
            "telemetry": {
                "temperature": self.temperature,
                "humidity": self.humidity,
                "light_level": self.light_level
            },
            "status": {
                "occupancy": self.occupancy,
                "lighting": self.lighting,
                "hvac_mode": self.hvac_mode
            }
        })


# ================= LOOP =================
async def room_loop(room, client):
    await asyncio.sleep(random.uniform(0, 2))  # startup delay
    counter = 0

    while True:
        room.update()

        topic = room.get_topic()
        payload = room.to_json()

        # Send telemetry
        client.publish(topic, payload)

        # Send heartbeat
        heartbeat_topic = topic.replace("telemetry", "heartbeat")
        client.publish(heartbeat_topic, '{"status": "alive"}')

        print(f"{room.room_id} | Temp: {room.temperature} | Light: {room.light_level} | LED: {room.lighting}")

        counter += 1

        if counter % 5 == 0:
            save_room(room)

        await asyncio.sleep(2)


# ================= MAIN =================
async def main():
    init_db()

    client = MQTTClient("world-engine")
    await client.connect(BROKER)

    saved_data = load_rooms()
    rooms = []

    for floor in range(1, CONFIG["num_floors"] + 1):
        for r in range(1, CONFIG["rooms_per_floor"] + 1):
            room_id = f"b01-f{floor:02d}-r{r:03d}"
            room = Room("b01", floor, room_id)

            # Restore data
            for row in saved_data:
                if row[0] == room_id:
                    room.temperature = row[1]
                    room.humidity = row[2]
                    room.hvac_mode = row[3]

            rooms.append(room)

    tasks = [asyncio.create_task(room_loop(room, client)) for room in rooms]

    await asyncio.gather(*tasks)


asyncio.run(main())
