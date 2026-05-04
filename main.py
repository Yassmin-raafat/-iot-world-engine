import asyncio
import json
import time
from gmqtt import Client

# 🔑 حطي التوكن بتاعك
TOKEN = "oscHuiQcuEX8Bwri1ZJ9"

# 🔥 الحالة العامة
hvac_state = False
temperature = 25.0

# 📩 استقبال الأوامر (RPC)
def on_message(client, topic, payload, qos, properties):
    global hvac_state

    print("RPC RECEIVED:", payload)

    data = json.loads(payload)

    # ON / OFF من dashboard
    hvac_state = data["params"]

    print("HVAC STATE:", hvac_state)

    # نبعت الحالة كـ telemetry
    client.publish("v1/devices/me/telemetry", json.dumps({
        "hvac": hvac_state
    }))

# 🚀 البرنامج الرئيسي
async def main():
    global temperature

    client = Client("world-engine")

    client.set_auth_credentials(TOKEN)

    # ربط الـ RPC
    client.on_message = on_message

    # الاتصال بـ ThingsBoard
    await client.connect("eu.thingsboard.cloud", 1883)

    print("CONNECTED SUCCESS")

    # الاشتراك في الأوامر
    client.subscribe("v1/devices/me/rpc/request/+")

    while True:
        # 🧠 logic بسيط للـ Digital Twin
        if hvac_state:
            temperature -= 0.3   # التكييف يقلل الحرارة
        else:
            temperature += 0.1   # الحرارة تزيد طبيعي

        # limits عشان تبقى realistic
        temperature = max(15, min(35, temperature))

        # 📡 إرسال telemetry
        data = {
            "temperature": round(temperature, 2),
            "hvac": hvac_state
        }

        client.publish("v1/devices/me/telemetry", json.dumps(data))

        print("Sent:", data)

        await asyncio.sleep(3)

# ▶️ تشغيل
asyncio.run(main())