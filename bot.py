#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import sys
import time

# ─── CONFIG ───────────────────────────────────
FIREBASE_API_KEY = "AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"

ENDPOINTS = {
    "1": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating1",
    "2": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating2",
    "5": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating5",
    "6": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating6",
}

BOT_TOKEN = "8951462015:AAHDQX147lh4Y3a-af5tWR-1W5oPhXiaXTc"
CHAT_ID = "8884756222"

G = "\033[92m"
Y = "\033[93m"
C = "\033[96m"
W = "\033[97m"
R = "\033[91m"
RE = "\033[0m"

# ─── HELPERS ──────────────────────────────────

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

def banner():
    os.system("clear")
    print(f"{G}##############################################")
    print(f"#                                            #")
    print(f"#        {W}CAR PARKING MULTIPLAYER             {G}#")
    print(f"#           {Y}KING RANK SERVICE                {G}#")
    print(f"#                                            #")
    print(f"#        {C}Instagram: ilija.jvcc                     {G}#")
    print(f"#        {C}Telegram: @ILIJASELL               {G}#")
    print(f"#                                            #")
    print(f"##############################################{RE}")
    print()
    print(f"{W}----------------------------------------------{RE}")
    print("1. King Rank ")
    print("2. Exit")
    print(f"{W}----------------------------------------------{RE}")

def login(email, password):
    payload = {
        "clientType": "CLIENT_TYPE_ANDROID",
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(FIREBASE_LOGIN_URL, headers=headers, json=payload, timeout=15)
        data = r.json()
        if r.status_code == 200 and "idToken" in data:
            return data["idToken"]
    except Exception as e:
        print(f"{R}[-] Login error: {e}{RE}")
    return None

def build_payload():
    rating_data = {k: 100000 for k in [
        "cars", "car_fix", "car_collided", "car_exchange", "car_trade", "car_wash",
        "slicer_cut", "drift_max", "drift", "cargo", "delivery", "taxi", "levels", "gifts",
        "fuel", "offroad", "speed_banner", "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", "push_ups", "burnt_tire", "passanger_distance"
    ]}
    rating_data["time"] = 100000000
    rating_data["race_win"] = 3000000
    return {"data": json.dumps({"RatingData": rating_data})}

def set_rank(token, url, name):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "okhttp/3.12.13",
    }
    try:
        r = requests.post(url, headers=headers, json=build_payload(), timeout=15)
        if r.status_code == 200:
            print(f"{G}[+] {name} → OK{RE}")
            return True
        else:
            print(f"{R}[-] {name} → FAILED ({r.status_code}){RE}")
            try:
                print(f"{R}    {r.json()}{RE}")
            except:
                print(f"{R}    {r.text[:200]}{RE}")
    except Exception as e:
        print(f"{R}[-] {name} → ERROR: {e}{RE}")
    return False

def send_all(token):
    print(f"\n{Y}[*] Sending to all endpoints...{RE}")
    ok = 0
    for key, url in ENDPOINTS.items():
        if set_rank(token, url, f"SetUserRating{key}"):
            ok += 1
    print(f"\n{G}[+] Success: {ok}/{len(ENDPOINTS)} endpoints{RE}")
    return ok == len(ENDPOINTS)

# ─── MAIN ─────────────────────────────────────

def main():
    while True:
        banner()
        choice = input(f"{W}Select an option: {RE}").strip()

        if choice == "1":
            email = input(f"{W}Enter Email: {RE}").strip()
            password = input(f"{W}Enter Password: {RE}").strip()

            print(f"\n{Y}[*] Connecting to Firebase...{RE}")
            auth_token = login(email, password)

            if not auth_token:
                print(f"\n{R}[-] Login failed! Check credentials.{RE}")
                time.sleep(2)
                continue

            print(f"{G}[+] Login successful!{RE}")
            time.sleep(0.5)

            if send_all(auth_token):
                send_telegram(f"✅ King Rank applied to {email}")

            print(f"\n{C}Press Enter to continue...{RE}")
            input()

        elif choice == "6":
            print(f"{Y}Exiting...{RE}")
            sys.exit(0)
        else:
            print(f"{R}Invalid option!{RE}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Y}\nInterrupted by user.{RE}")
        sys.exit(0)
