import asyncio
import json
import random
from gmqtt import Client

#  load tokens
with open("tokens.json") as f:
    devices = json.load(f)

print("TOTAL DEVICES:", len(devices))


async def simulate(device):
    token = device["token"]
    name = device["name"]

    client = Client(f"client_{name}")
    client.set_auth_credentials(token)

    try:
        await client.connect("host.docker.internal", 1883)
        print("✅ Connected:", name)
    except Exception as e:
        print("❌ Failed:", name, e)
        return

    temp = random.randint(20, 30)

    while True:
        temp += random.uniform(-0.5, 0.5)

        payload = {
            "temperature": round(temp, 2),
            "hvac": False
        }

        client.publish("v1/devices/me/telemetry", json.dumps(payload))
        print(f"📡 {name} -> {payload}")

        await asyncio.sleep(2)


async def main():
    tasks = []

    for d in devices:
        tasks.append(asyncio.create_task(simulate(d)))
        await asyncio.sleep(0.02)  

    await asyncio.gather(*tasks)


asyncio.run(main())