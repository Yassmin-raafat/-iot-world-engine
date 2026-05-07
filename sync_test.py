import asyncio
import json
from gmqtt import Client

TOKEN = "2aB4KP7x4iiWzdwmJp92"

hvac_state = False


def on_message(client, topic, payload, qos, properties):

    global hvac_state

    data = json.loads(payload.decode())

    print("\n MESSAGE")
    print("TOPIC:", topic)
    print("DATA:", data)

    if "shared" in data:

        shared = data["shared"]

        if "desired_hvac" in shared:

            desired = shared["desired_hvac"]

            print(f"\n DESIRED HVAC = {desired}")

            if desired != hvac_state:

                print("🔄 APPLYING DESIRED STATE")

                hvac_state = desired


async def main():

    client = Client("sync_test")

    client.set_auth_credentials(TOKEN)

    client.on_message = on_message

    await client.connect(
        "host.docker.internal",
        1883
    )

    print(" CONNECTED")

    client.subscribe(
        "v1/devices/me/attributes"
    )

    client.subscribe(
        "v1/devices/me/attributes/response/+"
    )

    client.publish(
        "v1/devices/me/attributes/request/1",
        json.dumps({
            "sharedKeys": "desired_hvac"
        })
    )

    print(" WAITING FOR ATTRIBUTE CHANGES")

    while True:

        client.publish(
            "v1/devices/me/attributes",
            json.dumps({
                "reported_hvac": hvac_state
            })
        )

        print(
            f" REPORTED HVAC = {hvac_state}"
        )

        await asyncio.sleep(3)


asyncio.run(main())