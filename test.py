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
FK       = " 'AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ'"
RANK_URL = "https://europe-west1-cpm-2-7cea1.cloudfunctions.net/ValidateRank23_1","https://europe-west1-cpm-2-7cea1.cloudfunctions.net/GetUserRatingCall22_1"

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
#Primerak skripte koja lepo radi samo sto je za cpm1        self.uid = uid
        self.headers = {
            "Authorization": f"Bearer {token}",
            "X-Firebase-Token": token,
            "Content-Type": "application/json",
            "User-Agent": CPM2_USER_AGENT,
        }

    def _call(self, endpoint, data=None):
        """Universal wrapper for calling Cloud Functions endpoints."""
        url = f"{CF_BASE_URL}/{endpoint}"
        payload = data if data is not None else {"localId": self.uid}
        try:
            res = _session.post(
                url, headers=self.headers, json=payload, timeout=15
            )
            try:
                return res.json()
            except:
                return {"status": res.status_code, "text": res.text}
        except Exception as e:
            return {"error": str(e)}

    # --- Active / Alternative Endpoints ---

    def get_user_rating(self):
        """Using working v22 version instead of offline v23."""
        return self._call("GetUserRatingCall22_1")

    def get_user_connection(self):
        """Using working GetUserConnectionData22_1 server."""
        return self._call("GetUserConnectionData22_1")

    def award_reward(self, reward_id=1):
        """Sending request to claim reward/coins."""
        payload = {"localId": self.uid, "rewardId": reward_id}
        return self._call("AwardReward23_1", payload)

    def claim_event_reward(self, event_id="current"):
        """Claiming event rewards."""
        payload = {"localId": self.uid, "eventId": event_id}
        return self._call("ClaimEventReward23_1", payload)

    def get_daily_task(self):
        """Fetching daily task status."""
        return self._call("GetDailyTaskCall23_1")

    def validate_rank(self):
        """Validating player rank."""
        return self._call("ValidateRank23_1")


# --- Example Usage ---
if __name__ == "__main__":
    EMAIL = "your_email@gmail.com"
    PASSWORD = "your_password"

    print("[*] Logging in to Firebase...")
    auth = cpm2_login(EMAIL, PASSWORD)

    if "error" in auth:
        print(f"[-] Login error: {auth['error']}")
    else:
        token = auth["token"]
        uid = auth["uid"]
        print(f"[+] Successful login! UID: {uid}")

        api = CPM2CloudFunctions(token, uid)

        # 1. Fetch rating (via v22 server)
        print("\n[*] Fetching rating (v22_1)...")
        rating_res = api.get_user_rating()
        print("Response:", json.dumps(rating_res, indent=2))

        # 2. Attempt reward claim
        print("\n[*] Attempting reward claim (AwardReward23_1)...")
        reward_res = api.award_reward(reward_id=1)
        print("Response:", json.dumps(reward_res, indent=2))

        # 3. Connection check
        print(
            "\n[*] Server connection check (GetUserConnectionData22_1)..."
        )
        conn_res = api.get_user_connection()
        print("Response:", json.dumps(conn_res, indent=2))

