#!/usr/bin/env python3
"""
CPM King Rank Setter
Postavlja max rank (King) na Car Parking Multiplayer račun.
Zahtijeva: pip install requests
"""

import requests
import json
import sys

# ── Config ────────────────────────────────────
FK       = "AIzaSyAe_aOVT1gSfmHKBrorFvX4fRwN5nODXVA"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating1"

GAME_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "X-Unity-Version": "2022.3.62f2",
}

# ── King Rank Payload ─────────────────────────
# Ove vrijednosti postavljaju sve statistike na max
KING_PAYLOAD = {
    "RatingData": {
        "time": 1e22,
        "cars": 1e16,
        "car_fix": 1e13,
        "car_collided": 1e12,
        "car_exchange": 1e13,
        "car_trade": 1e13,
        "car_wash": 1e13,
        "slicer_cut": 1e13,
        "drift_max": 1e14,
        "drift": 1e14,
        "cargo": 1e5,
        "delivery": 1e5,
        "race_win": 3e20,
        "taxi": 1e10,
        "levels": 10000990000,
        "gifts": 1e9,
        "fuel": 1e10,
        "offroad": 1e10,
        "speed_banner": 1e9,
        "reactions": 1e17,
        "run": 1e9,
        "real_estate": 1e9,
        "t_distance": 1e10,
        "treasure": 1e10,
        "block_post": 1e10,
        "push_ups": 1e12,
        "burnt_tire": 1e10,
        "passanger_distance": 1e8,
    }
}

# ── Functions ─────────────────────────────────

def login(email: str, password: str) -> tuple:
    """Firebase sign-in → (idToken, localId)"""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FK}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
        "clientType": "CLIENT_TYPE_ANDROID",
    }
    r = requests.post(url, json=payload, headers=GAME_HEADERS, timeout=30)
    data = r.json()

    if "idToken" not in data:
        err = data.get("error", {}).get("message", "UNKNOWN_ERROR")
        print(f"❌ Login failed: {err}")
        sys.exit(1)

    return data["idToken"], data.get("localId", "")


def set_king_rank(id_token: str) -> bool:
    """Pošalji King rank payload."""
    headers = {**GAME_HEADERS, "Authorization": f"Bearer {id_token}"}
    payload = {"data": json.dumps(KING_PAYLOAD)}

    r = requests.post(RANK_URL, json=payload, headers=headers, timeout=30)
    print(f"📡 Status: {r.status_code}")

    try:
        resp = r.json()
        print(f"📨 Response: {json.dumps(resp, indent=2)}")

        # CPM obično vraća {"result": 1} ili slično za uspjeh
        if any(resp.get(k) for k in ("result", "ok", "success")):
            print("✅ King rank postavljen!")
            return True
        else:
            print("⚠️ Neočekivani odgovor.")
            return False
    except Exception as e:
        print(f"⚠️ Greška pri parsiranju: {e}")
        print(f"Raw: {r.text}")
        return False


# ── Main ──────────────────────────────────────
if __name__ == "__main__":
    print("=" * 45)
    print("  👑  CPM KING RANK SETTER")
    print("=" * 45)

    email = input("📧 Email: ").strip()
    password = input("🔑 Password: ").strip()

    print("\n🔐 Login...")
    token, uid = login(email, password)
    print(f"✅ Ulogiran! UID: {uid}\n")

    print("👑 Postavljam King Rank...")
    set_king_rank(token)
