import asyncio
import json
import random
import sys
from gmqtt import Client

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

with open("tokens.json", "r", encoding="utf-8") as f:
    devices = json.load(f)

print("TOTAL DEVICES:", len(devices))


async def simulate(device):
    token = device["token"]
    name = device["name"]

    client = Client(f"client_{name}")
    client.set_auth_credentials(token, None)

    hvac_state = False
    connected = asyncio.Event()

    def on_connect(client, flags, rc, properties):
        print("Connected:", name)
        client.subscribe("v1/devices/me/rpc/request/+", qos=1)
        connected.set()

    def on_disconnect(client, packet, exc=None):
        print("Disconnected:", name, exc)
        connected.clear()

    def on_message(client, topic, payload, qos, properties):
        nonlocal hvac_state

        try:
            data = json.loads(payload.decode("utf-8"))

            print(f"RPC for {name}: {data}")

            method = data.get("method")
            params = data.get("params")

            if method == "setHvac":
                hvac_state = bool(params)
                print(f"HVAC for {name} set to {hvac_state}")

            request_id = topic.rsplit("/", 1)[-1]
            response_topic = f"v1/devices/me/rpc/response/{request_id}"

            client.publish(
                response_topic,
                json.dumps({"success": True, "hvac": hvac_state}),
                qos=1,
            )

        except Exception as e:
            print(f"RPC ERROR for {name}:", e)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        await client.connect("127.0.0.1", 1883, keepalive=60)
        await connected.wait()
    except Exception as e:
        print("Failed:", name, e)
        return

    temp = random.uniform(20, 30)

    await asyncio.sleep(random.uniform(0, 3))

    while True:
        try:
            temp += random.uniform(-0.5, 0.5)

            payload = {
                "temperature": round(temp, 2),
                "hvac": hvac_state,
            }

            client.publish(
                "v1/devices/me/telemetry",
                json.dumps(payload),
                qos=1,
            )

            print(f"{name} -> {payload}")

            await asyncio.sleep(2 + random.uniform(0, 1))

        except Exception as e:
            print(f"PUBLISH ERROR for {name}:", e)
            await asyncio.sleep(2)


async def main():
    tasks = [asyncio.create_task(simulate(d)) for d in devices]
    await asyncio.gather(*tasks)


asyncio.run(main())
