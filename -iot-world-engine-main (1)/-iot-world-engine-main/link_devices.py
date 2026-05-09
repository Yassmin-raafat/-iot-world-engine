import requests
import json

BASE_URL = "http://localhost:9090"
USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"

# LOGIN
res = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"username": USERNAME, "password": PASSWORD}
)
token = res.json()["token"]

headers = {
    "X-Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# LOAD DEVICES FROM TOKENS
with open("tokens.json") as f:
    devices = json.load(f)

# GET DEVICES
devices_data = requests.get(
    f"{BASE_URL}/api/tenant/devices?pageSize=200&page=0",
    headers=headers
).json()["data"]

# GET ASSETS WITH PAGINATION
assets_data = []
page = 0

while True:
    r = requests.get(
        f"{BASE_URL}/api/tenant/assets?pageSize=100&page={page}",
        headers=headers
    ).json()

    assets_data.extend(r["data"])

    if not r["hasNext"]:
        break

    page += 1

# FILTER ONLY B01 ROOMS
rooms = [a for a in assets_data if a["type"] == "room" and a["name"].lower().startswith("b01-")]

# SORT BOTH LISTS
devices_data.sort(key=lambda x: x["name"])
rooms.sort(key=lambda x: x["name"])

# LINK FUNCTION
def link(room_id, device_id):
    requests.post(
        f"{BASE_URL}/api/relation",
        json={
            "from": {"id": room_id, "entityType": "ASSET"},
            "to": {"id": device_id, "entityType": "DEVICE"},
            "type": "Contains"
        },
        headers=headers
    )

# LINK BY ORDER
count = 0

for d, r in zip(devices_data, rooms):
    link(r["id"]["id"], d["id"]["id"])
    print(f"Linked {d['name']} → {r['name']}")
    count += 1

print(f"\nDONE  Total linked: {count}")