import requests
import json
import random

BASE_URL = "http://localhost:9090"
USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"

# ================= LOGIN =================
res = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"username": USERNAME, "password": PASSWORD}
)

token = res.json()["token"]

headers = {
    "X-Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# ================= CREATE ASSET =================
def create_asset(name, asset_type, parent_id=None):
    r = requests.post(
        f"{BASE_URL}/api/asset",
        json={"name": name, "type": asset_type},
        headers=headers
    )
    asset_id = r.json()["id"]["id"]
    if parent_id:
        create_relation(parent_id, "ASSET", asset_id, "ASSET")
    return asset_id

# ================= CREATE RELATION =================
def create_relation(from_id, from_type, to_id, to_type):
    requests.post(
        f"{BASE_URL}/api/relation",
        json={
            "from": {"id": from_id, "entityType": from_type},
            "to": {"id": to_id, "entityType": to_type},
            "type": "Contains"
        },
        headers=headers
    )

# ================= CREATE ATTRIBUTE =================
def set_attributes(asset_id):
    data = {
        "square_footage": random.randint(30, 60),
        "occupant_capacity": random.randint(10, 40),
        "coordinates_x": random.randint(0, 500),
        "coordinates_y": random.randint(0, 500),
        "room_type": random.choice(["lab", "office", "lecture"])
    }

    requests.post(
        f"{BASE_URL}/api/plugins/telemetry/ASSET/{asset_id}/attributes/SERVER_SCOPE",
        json=data,
        headers=headers
    )

# ================= MAIN =================
print("Creating Campus...")
campus_id = create_asset("ZC-Main-Campus", "campus")

for building_num in range(1, 2):  # Example: 2 buildings
    building_id = create_asset(f"B{building_num:02}", "building", campus_id)
    for floor_num in range(1, 11):  # Example: 10 floors per building
        floor_id = create_asset(f"B{building_num:02}-F{floor_num:02}", "floor", building_id)
        for room_num in range(1, 21):  # Example: 20 rooms per floor
            room_id = create_asset(f"B{building_num:02}-F{floor_num:02}-R{room_num:03}", "room", floor_id)
            set_attributes(room_id)

print("DONE ")