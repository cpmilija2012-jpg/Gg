import json
import requests

# Core constants
CPM2_API_KEY = "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ"
CF_BASE_URL = "https://europe-west1-cpm-2-7cea1.cloudfunctions.net"
CPM2_USER_AGENT = (
    "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)"
)

_session = requests.Session()


def cpm2_login(email, pw):
    """Logs in to Firebase and returns the ID Token and LocalID (UID)."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={CPM2_API_KEY}"
    payload = {
        "email": email,
        "password": pw,
        "returnSecureToken": True,
        "clientType": "CLIENT_TYPE_ANDROID",
    }
    try:
        r = _session.post(url, json=payload, timeout=20)
        j = r.json()
        if "idToken" in j:
            return {"token": j["idToken"], "uid": j["localId"]}
        return {"error": j.get("error", {}).get("message", "Login failed")}
    except Exception as e:
        return {"error": str(e)}


class CPM2CloudFunctions:

    def __init__(self, token, uid):
        self.token = token
        self.uid = uid
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

