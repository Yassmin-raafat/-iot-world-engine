import requests
import json

BASE_URL = "http://localhost:9090"

USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"

# 🔐 login
res = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"username": USERNAME, "password": PASSWORD}
)

token = res.json()["token"]

headers = {
    "X-Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

devices = []

# 🏢 create 200 rooms (10 floors × 20 rooms)
for floor in range(1, 11):
    for room in range(1, 21):
        name = f"b01-f{floor:02d}-r{room:03d}"

        r = requests.post(
            f"{BASE_URL}/api/device",
            json={"name": name, "type": "default"},
            headers=headers
        )

        if r.status_code != 200:
            print("Error:", name)
            print(r.text)
            continue

        device_id = r.json()["id"]["id"]

        # 🔑 get token
        cred = requests.get(
            f"{BASE_URL}/api/device/{device_id}/credentials",
            headers=headers
        ).json()

        devices.append({
            "name": name,
            "token": cred["credentialsId"]
        })

        print("Created:", name)

# 💾 save tokens
with open("tokens.json", "w") as f:
    json.dump(devices, f, indent=2)

print("\n🔥 DONE:", len(devices), "devices created")