import requests
import json
import time
from datetime import datetime

# --- CONFIGURATION ---
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

# Your Telegram Bot Details
BOT_TOKEN = "8691576277:AAG97ec5y9SmEPfWunG_GXwzbdRlPVWQd-s"
CHAT_ID = 7183809303

def send_to_telegram(message):
    """Sends a notification to your Telegram bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
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
        response_data = response.json()
        if response.status_code == 200 and 'idToken' in response_data:
            return response_data.get('idToken')
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

def show_menu():
    print("\n" + "="*35)
    print("      CPM KING RANK SERVICE")
    print("="*35)
    print("1. King Rank")
    print("2. Exit")
    print("="*35)
    return input("Select an option: ")

def main_logic():
    while True:
        choice = show_menu()
        
        if choice == "1":
            email = input("\nEmail: ").strip()
            password = input("Password: ").strip()
            
            print("\nConnecting to server...")
            auth_token = login(email, password)
            
            if auth_token:
                print("Applying King Rank...")
                if set_rank(auth_token):
                    # Notify your bot about the successful update
                    log_msg = f"✅ Success: King Rank applied to {email}"
                    send_to_telegram(log_msg)
                    print("Success! Your account now has King Rank.")
                else:
                    print("Error: Could not apply rank.")
            else:
                print("Login failed! Invalid credentials.")
                
        elif choice == "2":
            print("Exiting tool... Goodbye!")
            break
        else:
            print("Invalid option. Please choose 1 or 2.")

if __name__ == "__main__":
    main_logic()
