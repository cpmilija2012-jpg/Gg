import requests
import json
import getpass
import time
from datetime import datetime
import os

FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"
CLAN_ID_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/GetClanId"

BOT_TOKEN = "8224919170:AAFsIZt5dhxtpZbESW8W9SZUf441AShb4WU"
CHAT_ID = 7964340522

def print_banner():
    os.system('clear')
    print("="*45)
    print("       🚀 ANONYMO CPM SERVICE 🚀")
    print("="*45)
    print(f"📸 Instagram: @anonymo.cpm")
    print(f"✈️  Telegram:  @Anonymo123456")
    print("="*45)
    print("        KING RANK ACTIVATOR - CPM 1")
    print("="*45 + "\n")

def send_to_telegram():
    return

def login(email, password):
    payload = {
        "clientType": "CLIENT_TYPE_ANDROID",
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(FIREBASE_LOGIN_URL, headers=headers, json=payload)
        response_data = response.json()
        if response.status_code == 200 and 'idToken' in response_data:
            return response_data.get('idToken')
        else:
            print("❌ Neuspešna prijava. Proveri podatke.")
            return None
    except requests.exceptions.RequestException:
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
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "okhttp/3.12.13"
    }
    try:
        response = requests.post(RANK_URL, headers=headers, json=payload)
        if response.status_code == 200:
            print("✅ KING RANK uspešno aktiviran!")
        else:
            print(f"❌ Greška pri setovanju ranka: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def main_logic():
    print_banner()
    while True:
        try:
            email = input("📧 Unesite Email: ").strip()
            password = input("🔑 Unesite Password: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
            
        print("\n⏳ Provera podataka...")
        auth_token = login(email, password)
        if auth_token:
            set_rank(auth_token)
        
        print("\n" + "-"*45)
        choice = input("Želite li još jedan nalog? (y/n): ")
        if choice.lower() != 'y':
            break
        print_banner()

if __name__ == "__main__":
    main_logic()
