import requests
import json

# =========================
# THINGSBOARD CLOUD
# =========================
BASE_URL = "https://eu.thingsboard.cloud"

# =========================
# YOUR ACCOUNT
# =========================
USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"



# =========================
# LOGIN
# =========================
res = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "username": USERNAME,
        "password": PASSWORD
    }
)

if res.status_code != 200:

    print("❌ Login failed")

    print(res.text)

    exit()

token = res.json()["token"]

headers = {
    "X-Authorization":
    f"Bearer {token}",

    "Content-Type":
    "application/json"
}

print("✅ Logged in")

# =========================
# GET ALL DEVICES
# =========================
devices = []

page = 0

page_size = 100

while True:

    res = requests.get(
        f"{BASE_URL}"
        f"/api/tenant/devices"
        f"?pageSize={page_size}"
        f"&page={page}",

        headers=headers
    )

    if res.status_code != 200:

        print(
            "❌ Failed to fetch devices"
        )

        print(res.text)

        exit()

    data = res.json()

    devices.extend(
        data["data"]
    )

    if not data.get("hasNext"):

        break

    page += 1

print(
    f"📦 Total devices found:"
    f" {len(devices)}"
)

# =========================
# GET TOKENS
# =========================
result = []

for d in devices:

    device_id = d["id"]["id"]

    name = d["name"]

    cred_res = requests.get(
        f"{BASE_URL}"
        f"/api/device/"
        f"{device_id}"
        f"/credentials",

        headers=headers
    )

    if cred_res.status_code != 200:

        print(
            f"❌ Failed token for {name}"
        )

        continue

    cred = cred_res.json()

    device_token = (
        cred.get(
            "credentialsId"
        )
    )

    if not device_token:

        print(
            f"❌ No token for {name}"
        )

        continue

    result.append({
        "name": name,
        "token": device_token
    })

    print(
        f"🔑 Token fetched:"
        f" {name}"
    )

# =========================
# SAVE TOKENS
# =========================
with open(
    "tokens.json",
    "w"
) as f:

    json.dump(
        result,
        f,
        indent=2
    )

print(
    f"\n🎉 DONE!"
    f" tokens.json created"
    f" with {len(result)} devices"
)