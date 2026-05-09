
import asyncio
import json
import random
import sys
import hashlib

from gmqtt import Client

# =========================
# THINGSBOARD CLOUD
# =========================
TB_HOST = "eu.thingsboard.cloud"
TB_PORT = 1883

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

# =========================
# LOAD TOKENS
# =========================
with open("tokens.json", "r", encoding="utf-8") as f:
    devices = json.load(f)

print("TOTAL DEVICES:", len(devices))


async def simulate(device):

    token = device["token"]
    name = device["name"]

    # =========================
    # PARAMETERS
    # =========================
    alpha = 0.4
    beta = 1.2

    current_version = "1.0"
    target_version = "1.0"

    hvac_state = False

    client = Client(f"client_{name}")

    client.set_auth_credentials(
        token,
        None
    )

    connected = asyncio.Event()

    # =========================
    # CONNECT
    # =========================
    def on_connect(client, flags, rc, properties):

        print("Connected:", name)

        client.subscribe(
            "v1/devices/me/rpc/request/+",
            qos=1
        )

        connected.set()

    # =========================
    # DISCONNECT
    # =========================
    def on_disconnect(client, packet, exc=None):

        print("Disconnected:", name)

        connected.clear()

    # =========================
    # MESSAGE HANDLER
    # =========================
    def on_message(
        client,
        topic,
        payload,
        qos,
        properties
    ):

        nonlocal hvac_state
        nonlocal alpha
        nonlocal beta
        nonlocal current_version
        nonlocal target_version

        try:

            data = json.loads(
                payload.decode("utf-8")
            )

            print(
                f"RPC for {name}:",
                data
            )

            method = data.get("method")

            params = data.get("params")

            # =========================
            # HVAC RPC
            # =========================
            if method == "setHvac":

                hvac_state = bool(params)

                print(
                    f"HVAC for {name} "
                    f"set to {hvac_state}"
                )

            # =========================
            # OTA UPDATE
            # =========================
            elif method == "otaUpdate":

                print("OTA RECEIVED")

                received_hash = params["hash"]

                config = params["config"]

                calculated_hash = hashlib.sha256(
                    json.dumps(
                        config,
                        sort_keys=True
                    ).encode()
                ).hexdigest()

                # =========================
                # SECURITY CHECK
                # =========================
                if received_hash != calculated_hash:

                    print(
                        "TAMPERING DETECTED"
                    )

                    client.publish(
                        "v1/devices/me/telemetry",
                        json.dumps({
                            "security_alert": True
                        }),
                        qos=1
                    )

                    return

                print("HASH VERIFIED")

                alpha = config["alpha"]

                beta = config["beta"]

                target_version = (
                    config["version"]
                )

                current_version = (
                    target_version
                )

                print(
                    f"UPDATED -> "
                    f"alpha={alpha}, "
                    f"beta={beta}, "
                    f"version={current_version}"
                )

                # =========================
                # SEND VERSION
                # =========================
                client.publish(
                    "v1/devices/me/attributes",
                    json.dumps({
                        "current_version":
                        current_version
                    }),
                    qos=1
                )

                # =========================
                # SUCCESS TELEMETRY
                # =========================
                client.publish(
                    "v1/devices/me/telemetry",
                    json.dumps({
                        "ota_update_success": True,
                        "alpha": alpha,
                        "beta": beta,
                        "current_version":
                        current_version
                    }),
                    qos=1
                )

            # =========================
            # RPC RESPONSE
            # =========================
            request_id = (
                topic.rsplit("/", 1)[-1]
            )

            response_topic = (
                f"v1/devices/me/"
                f"rpc/response/"
                f"{request_id}"
            )

            client.publish(
                response_topic,
                json.dumps({
                    "success": True
                }),
                qos=1
            )

        except Exception as e:

            print(
                f"ERROR for {name}:",
                e
            )

    client.on_connect = on_connect

    client.on_disconnect = on_disconnect

    client.on_message = on_message

    # =========================
    # CONNECT
    # =========================
    try:

        await client.connect(
            TB_HOST,
            TB_PORT,
            keepalive=60
        )

        await connected.wait()

    except Exception as e:

        print(
            "Failed:",
            name,
            e
        )

        return

    # =========================
    # INITIAL TEMP
    # =========================
    temp = random.uniform(20, 30)

    await asyncio.sleep(
        random.uniform(0, 3)
    )

    # =========================
    # MAIN LOOP
    # =========================
    while True:

        try:

            if hvac_state:
                temp -= alpha
            else:
                temp += 0.1

            temp += random.uniform(
                -0.3,
                0.3
            )

            temp = max(
                15,
                min(35, temp)
            )

            payload = {
                "temperature":
                round(temp, 2),

                "hvac":
                hvac_state,

                "alpha":
                alpha,

                "beta":
                beta
            }

            client.publish(
                "v1/devices/me/telemetry",
                json.dumps(payload),
                qos=1
            )

            print(
                f"{name} -> {payload}"
            )

            await asyncio.sleep(2)

        except Exception as e:

            print(
                f"PUBLISH ERROR "
                f"for {name}:",
                e
            )

            await asyncio.sleep(2)


async def main():

    tasks = [
        asyncio.create_task(
            simulate(d)
        )
        for d in devices
    ]

    await asyncio.gather(*tasks)


asyncio.run(main())

