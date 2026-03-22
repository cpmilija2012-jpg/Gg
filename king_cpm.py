import requests
import json
import os

# --- CONFIGURATION ---
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

# Your Telegram Bot Details
BOT_TOKEN = "8691576277:AAG97ec5y9SmEPfWunG_GXwzbdRlPVWQd-s"
CHAT_ID = 7183809303

# ANSI Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
WHITE = '\033[97m'
RESET = '\033[0m'

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

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
        res_data = response.json()
        if response.status_code == 200 and 'idToken' in res_data:
            return res_data.get('idToken')
        return None
    except:
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
        response = requests.post(RANK_URL, headers=headers, json=payload)
        return response.status_code == 200
    except:
        return False

def show_banner():
    os.system('clear')
    print(f"{GREEN}##############################################")
    print(f"#                                            #")
    print(f"#        {WHITE}CAR PARKING MULTIPLAYER             {GREEN}#")
    print(f"#           {YELLOW}KING RANK SERVICE                {GREEN}#")
    print(f"#                                            #")
    print(f"#        {CYAN}IG: @anonymo.cpm                    {GREEN}#")
    print(f"#        {CYAN}Owner: @anonymo.cpm                 {GREEN}#")
    print(f"#                                            #")
    print(f"##############################################{RESET}")
    print(f"\n{WHITE}----------------------------------------------{RESET}")
    print(f"1. King Rank")
    print(f"2. Exit")
    print(f"{WHITE}----------------------------------------------{RESET}")

def main_logic():
    while True:
        show_banner()
        choice = input(f"{WHITE}Select an option: {RESET}")
        
        if choice == "1":
            email = input(f"{WHITE}Enter Email: {RESET}").strip()
            password = input(f"{WHITE}Enter Password: {RESET}").strip()
            
            print(f"\n{YELLOW}Connecting to server...{RESET}")
            auth_token = login(email, password)
            
            if auth_token:
                print(f"{CYAN}Applying King Rank...{RESET}")
                if set_rank(auth_token):
                    log_msg = f"✅ Success: King Rank applied to {email}"
                    send_to_telegram(log_msg)
                    print(f"{GREEN}Success! King Rank is now active.{RESET}")
                    time.sleep(2)
                else:
                    print(f"\033[91mError: Could not update rank.{RESET}")
                    time.sleep(2)
            else:
                print(f"\033[91mLogin failed! Check credentials.{RESET}")
                time.sleep(2)
                
        elif choice == "2":
            print(f"{YELLOW}Exiting...{RESET}")
            break
        else:
            print(f"\033[91mInvalid option.{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    import time
    main_logic()
