import asyncio
import random
import json
from gmqtt import Client as MQTTClient
import sqlite3
import time

BROKER = "test.mosquitto.org"


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

    def update(self):
        outside_temp = 30

        # thermal model
        leakage = 0.01 * (outside_temp - self.temperature)

        if self.hvac_mode == "ON":
            change = 0.5
        elif self.hvac_mode == "ECO":
            change = 0.2
        else:
            change = 0

        self.temperature += leakage + change

        # occupancy
        self.occupancy = random.choice([True, False])

        # ================= FAULTS =================

        # sensor drift
        if random.random() < 0.05:
            self.temperature += random.uniform(-1, 1)

        # frozen sensor
        if random.random() < 0.02:
            return

        # delay fault (simulate lag)
        if random.random() < 0.03:
            time.sleep(0.5)

    def get_topic(self):
        return f"campus/bldg_01/floor_{self.floor_id:02d}/room_{self.room_id[-3:]}/telemetry"

    def to_json(self):
        return json.dumps({
            "room_id": self.room_id,
            "temperature": round(self.temperature, 2),
            "humidity": self.humidity,
            "occupancy": self.occupancy,
            "hvac_mode": self.hvac_mode
        })


# ================= LOOP =================
async def room_loop(room, client):
    await asyncio.sleep(random.uniform(0, 2))

    counter = 0

    while True:
        room.update()

        # ✅ هنا نحط delay fault
        if random.random() < 0.03:
            await asyncio.sleep(0.5)

        topic = room.get_topic()
        payload = room.to_json()

        client.publish(topic, payload)

        heartbeat_topic = topic.replace("telemetry", "heartbeat")
        client.publish(heartbeat_topic, '{"status": "alive"}')

        print(f"{room.room_id} | Temp: {room.temperature:.2f}")

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

    # 🔥 200 ROOMS
    for floor in range(1, 11):      # 10 floors
        for r in range(1, 21):      # 20 rooms each
            room_id = f"b01-f{floor:02d}-r{r:03d}"
            room = Room("b01", floor, room_id)

            # restore saved state
            for row in saved_data:
                if row[0] == room_id:
                    room.temperature = row[1]
                    room.humidity = row[2]
                    room.hvac_mode = row[3]

            rooms.append(room)

    tasks = []
    for room in rooms:
        tasks.append(asyncio.create_task(room_loop(room, client)))

    await asyncio.gather(*tasks)


asyncio.run(main())