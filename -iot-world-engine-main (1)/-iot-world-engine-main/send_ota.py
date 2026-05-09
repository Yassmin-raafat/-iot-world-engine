import json
import hashlib
import asyncio

from gmqtt import Client

TB_HOST = "eu.thingsboard.cloud"
TB_PORT = 1883

# =========================
# DEVICE TOKEN
# =========================
TOKEN = "IZOgJ2ENVFt51lA1YYth"

# =========================
# OTA CONFIG
# =========================
config = {
    "alpha": 0.9,
    "beta": 2.0,
    "version": "1.1"
}

# =========================
# HASH
# =========================
hash_value = hashlib.sha256(
    json.dumps(
        config,
        sort_keys=True
    ).encode()
).hexdigest()

payload = {
    "config": config,
    "hash": hash_value
}


async def main():

    client = Client("ota_sender")

    # IMPORTANT
    client.set_auth_credentials(
        TOKEN,
        None
    )

    await client.connect(
        TB_HOST,
        TB_PORT
    )

    topic = "campus/b01/ota/config"

    client.publish(
        topic,
        json.dumps(payload),
        qos=1
    )

    print("OTA SENT")
    print(payload)

    await asyncio.sleep(2)

    await client.disconnect()


asyncio.run(main())
