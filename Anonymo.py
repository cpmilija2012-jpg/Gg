import requests
import json
import getpass
import time
import os
from datetime import datetime

# --- BRANDING & BANNER (English Version) ---
def screen_clear():
    # Clears the Termux terminal screen
    os.system('clear')

def show_banner():
    print("""
\033[1;32m  ###########################################
\033[1;32m  #                                         #
\033[1;32m  #        \033[1;37mCAR PARKING MULTIPLAYER\033[1;32m          #
\033[1;32m  #           \033[1;33mKING RANK SERVICE\033[1;32m             #
\033[1;32m  #                                         #
\033[1;32m  #       \033[1;36mIG: @anonymo.cpm\033[1;32m                  #
\033[1;32m  #       \033[1;36mOwner: @anonymo.cpm\033[1;32m               #
\033[1;32m  #                                         #
\033[1;32m  ###########################################
\033[0m
    """)

# --- ORIGINAL DATA (UNTouched) ---
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"
CLAN_ID_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/GetClanId"

BOT_TOKEN = "8224919170:AAFsIZt5dhxtpZbESW8W9SZUf441AShb4WU"
CHAT_ID = 7964340522

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
            print("\033[1;31mError: Invalid email or password.\033[0m")
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
        print("\033[1;33mSending King Rank request...\033[0m")
        response = requests.post(RANK_URL, headers=headers, json=payload)
        if response.status_code == 200:
            print("\033[1;32mSUCCESS: King Rank added to account!\033[0m")
            return True
        else:
            print("\033[1;31mError: Failed to set rank.\033[0m")
            return False
    except requests.exceptions.RequestException:
        return False

def main_logic():
    screen_clear()
    show_banner()
    while True:
        try:
            print("-" * 40)
            email = input("\033[1;37mEnter Email: \033[0m").strip()
            password = input("\033[1;37mEnter Password: \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
        
        auth_token = login(email, password)
        if auth_token:
            set_rank(auth_token)
            print("-" * 40)
            input("\nPress Enter for another account or Ctrl+C to exit...")
            screen_clear()
            show_banner()

if __name__ == "__main__":
    main_logic()

