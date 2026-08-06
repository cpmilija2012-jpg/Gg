#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║           CPM2 ULTIMATE TOOL v2.0                            ║
║  King Rank + Wallet + Garage + Custom API Caller             ║
║  Za Termux / Linux / Windows                                 ║
╚══════════════════════════════════════════════════════════════╝
"""

import requests
import json
import os
import sys
import time

# ============================================================
# KONFIGURACIJA - OVDJE MOŽEŠ MJENJATI
# ============================================================
FIREBASE_API_KEY = 'AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ'
BASE_URL = 'https://europe-west1-cpm-2-7cea1.cloudfunctions.net'
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"

# Telegram (ostavi prazno ako ne želiš)
BOT_TOKEN = ""
CHAT_ID = ""

# Session token (čuva se dok je program aktivan)
_session_token = None
_session_email = None

# ============================================================
# ANSI BOJE
# ============================================================
G = '\033[92m'   # Zelena
Y = '\033[93m'   # Zuta
C = '\033[96m'   # Cyan
R = '\033[91m'   # Crvena
M = '\033[95m'   # Magenta
W = '\033[97m'   # Bijela
B = '\033[94m'   # Plava
D = '\033[90m'   # Tamno siva
RESET = '\033[0m'
BOLD = '\033[1m'

# ============================================================
# POMOĆNE FUNKCIJE
# ============================================================
def clear():
    os.system('clear' if os.name != 'nt' else 'cls')

def banner():
    clear()
    print(f"""{C}
    ╔══════════════════════════════════════════════════╗
    ║                                                  ║
    ║   {W}██████╗ ██████╗ ███╗   ███╗{C}2 {W}ÜLTIMATE TOOL{C}   ║
    ║   {W}██╔════╝██╔═══██╗████╗ ████║{C}                  ║
    ║   {W}██║     ██║   ██║██╔████╔██║{C}  King Rank +    ║
    ║   {W}██║     ██║   ██║██║╚██╔╝██║{C}  Wallet +       ║
    ║   {W}╚██████╗╚██████╔╝██║ ╚═╝ ██║{C}  Garage         ║
    ║    {W}╚═════╝ ╚═════╝ ╚═╝     ╚═╝{C}                 ║
    ║                                                  ║
    ╚══════════════════════════════════════════════════╝{RESET}
    """)

def log(msg, type="info"):
    prefix = {
        "info": f"{C}[*]{RESET}",
        "ok": f"{G}[✓]{RESET}",
        "warn": f"{Y}[!]{RESET}",
        "error": f"{R}[✗]{RESET}",
        "input": f"{M}[?]{RESET}"
    }.get(type, f"{C}[*]{RESET}")
    print(f"{prefix} {msg}")

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def firebase_login(email, password):
    """Firebase login - vraća idToken."""
    payload = {
        "clientType": "CLIENT_TYPE_ANDROID",
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; CPM2)",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    try:
        log("Povezivanje na Firebase...", "info")
        r = requests.post(FIREBASE_LOGIN_URL, headers=headers, json=payload, timeout=30)
        data = r.json()
        if r.status_code == 200 and 'idToken' in data:
            return data['idToken']
        else:
            error = data.get('error', {}).get('message', 'Nepoznata greška')
            log(f"Firebase greška: {error}", "error")
            return None
    except Exception as e:
        log(f"Network greška: {e}", "error")
        return None

def api_call(endpoint, data=None, use_token=True):
    """Poziv CPM2 Cloud Function."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "okhttp/4.12.0",
        "x-api-key": FIREBASE_API_KEY
    }
    if use_token and _session_token:
        headers["Authorization"] = f"Bearer {_session_token}"
    
    payload = data if data is not None else {}
    
    try:
        log(f"Šaljem → {Y}{endpoint}{RESET}", "info")
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if r.status_code == 200:
            log(f"Status: {G}{r.status_code}{RESET}", "ok")
        else:
            log(f"Status: {R}{r.status_code}{RESET}", "error")
        
        # Pokušaj parsirati JSON
        try:
            return r.status_code, r.json()
        except:
            return r.status_code, r.text
            
    except Exception as e:
        log(f"Greška u pozivu: {e}", "error")
        return 0, str(e)

def ensure_login():
    """Provjeri je li korisnik logiran, ako ne - pitaj za login."""
    global _session_token, _session_email
    if _session_token:
        return True
    
    log("Nisi logiran. Unesi podatke:", "warn")
    email = input(f"{M}[?]{RESET} Email: ").strip()
    password = input(f"{M}[?]{RESET} Password: ").strip()
    
    if not email or not password:
        log("Prazan unos!", "error")
        return False
    
    token = firebase_login(email, password)
    if token:
        _session_token = token
        _session_email = email
        log("Uspješna prijava!", "ok")
        send_telegram(f"🔑 <b>CPM2 Login:</b> {email}")
        return True
    return False

def pretty_print(data):
    """Lijep ispis JSON-a."""
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)

# ============================================================
# MODULI
# ============================================================

def mod_king_rank():
    """Postavi King Rank - max sve statistike."""
    if not ensure_login():
        return
    
    log("Priprema King Rank payloada...", "info")
    
    # RatingData struktura (bazirano na CPM1, prilagođeno za CPM2)
    rating_data = {k: 100000 for k in [
        "cars", "car_fix", "car_collided", "car_exchange", 
        "car_trade", "car_wash", "slicer_cut", "drift_max", 
        "drift", "cargo", "delivery", "taxi", "levels", 
        "gifts", "fuel", "offroad", "speed_banner", 
        "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", 
        "push_ups", "burnt_tire", "passanger_distance",
        "race_drags", "race_circuits", "car_photos", 
        "car_tunes", "car_vinyls", "car_plates"
    ]}
    rating_data["time"] = 999999999
    rating_data["race_win"] = 9999
    rating_data["race_lose"] = 0
    rating_data["rating"] = 1000000
    
    # CPM1 šalje data kao JSON string unutar JSON-a
    payload = {"data": json.dumps({"RatingData": rating_data})}
    
    status, resp = api_call("SetUserRating23_1", payload)
    
    if status == 200:
        log("King Rank uspješno postavljen!", "ok")
        send_telegram(f"👑 <b>King Rank:</b> {_session_email}")
    else:
        log("Neuspješno postavljanje ranka.", "error")
        pretty_print(resp)

def mod_max_wallet():
    """Postavi novac i coinse na max."""
    if not ensure_login():
        return
    
    log("Postavljam wallet...", "info")
    
    # Pretpostavljena struktura za SaveWalletData23_1
    wallet = {
        "Money": 999999999,
        "Coins": 999999999
    }
    payload = {"data": json.dumps(wallet)}
    
    status, resp = api_call("SaveWalletData23_1", payload)
    
    if status == 200:
        log("Wallet ažuriran!", "ok")
        log(f"Novac: {G}999,999,999${RESET} | Coinsi: {G}999,999,999{RESET}", "ok")
        send_telegram(f"💰 <b>Max Wallet:</b> {_session_email}")
    else:
        log("Greška pri ažuriranju walleta.", "error")
        pretty_print(resp)

def mod_get_money_coins():
    """Dohvati trenutni novac i coinse."""
    if not ensure_login():
        return
    
    log("Dohvaćam novac...", "info")
    status_m, resp_m = api_call("GetMoney23_1", {})
    
    log("Dohvaćam coinse...", "info")
    status_c, resp_c = api_call("GetCoins23_1", {})
    
    print(f"\n{BOLD}{Y}━ WALLET INFO ━{RESET}")
    print(f"{C}Money:{RESET}")
    pretty_print(resp_m)
    print(f"\n{C}Coins:{RESET}")
    pretty_print(resp_c)

def mod_garage_info():
    """Provjeri garažu."""
    if not ensure_login():
        return
    
    status, resp = api_call("CheckGarage23_1", {})
    print(f"\n{BOLD}{Y}━ GARAŽA ━{RESET}")
    pretty_print(resp)

def mod_get_all_cars():
    """Dohvati listu svih auta iz baze."""
    if not ensure_login():
        return
    
    status, resp = api_call("GetAllCars23_1", {})
    print(f"\n{BOLD}{Y}━ SVA AUTA U BAZI ━{RESET}")
    pretty_print(resp)
    
    # Spremi u file za pregled
    try:
        with open("cpm2_all_cars.json", "w", encoding="utf-8") as f:
            json.dump(resp, f, indent=2, ensure_ascii=False)
        log("Spremljeno u cpm2_all_cars.json", "ok")
    except:
        pass

def mod_account_info():
    """Dohvati podatke o računu."""
    if not ensure_login():
        return
    
    status, resp = api_call("GetUserConnectionData23_1", {})
    print(f"\n{BOLD}{Y}━ RAČUN ━{RESET}")
    pretty_print(resp)

def mod_delete_account():
    """Obriši račun - OPASNO!"""
    if not ensure_login():
        return
    
    log(f"{R}{BOLD}UPOZORENJE: Ovo će OBRISATI tvoj račun!{RESET}", "warn")
    confirm = input(f"{R}[!]{RESET} Upiši 'DELETE' za potvrdu: ").strip()
    
    if confirm == "DELETE":
        status, resp = api_call("DeleteAccount23_1", {})
        if status == 200:
            log("Račun obrisan.", "ok")
            global _session_token, _session_email
            _session_token = None
            _session_email = None
        else:
            log("Neuspješno brisanje.", "error")
            pretty_print(resp)
    else:
        log("Otkazano.", "info")

def mod_custom_call():
    """Pozovi bilo koji endpoint s custom payloadom."""
    if not ensure_login():
        return
    
    print(f"\n{D}Dostupni endpointi:{RESET}")
    endpoints = [
        "AreCarsDesynchronized23_1", "AwardReward23_1", "BuyCar23_1",
        "BuyCoins21_1", "BuyMoney21_1", "ClaimEventReward23_1",
        "ExchangeCarForMoney23_1", "GetAllCurrentEvents23_1",
        "GetCarPrice23_1", "GetDailyTaskCall23_1", "GetPlayerRecords23_1",
        "GetRewards23_1", "GetUserRatingCall23_1", "HasPurchaseHistory23_1",
        "MPSellCar23_1", "PurchaseInAppItem23_1", "RestorePurchase23_1",
        "SaveCar23_1", "SaveEngineInventory23_1", "SavePartsInventory23_1",
        "SavePlateVinyls23_1", "SavePlayerRecords23_1", "SellGarage23_1",
        "SetCircuitRacing23_1", "SetDragRacing23_1", "SpendCoins23_1",
        "SubmitEventRecord23_1", "ValidateRank23_1"
    ]
    for i, ep in enumerate(endpoints, 1):
        print(f"  {C}{i:2}.{RESET} {ep}")
    
    ep_input = input(f"\n{M}[?]{RESET} Endpoint ime (ili broj iz liste): ").strip()
    
    # Ako je broj, pretvori
    if ep_input.isdigit():
        idx = int(ep_input) - 1
        if 0 <= idx < len(endpoints):
            ep_input = endpoints[idx]
        else:
            log("Nevažeći broj.", "error")
            return
    
    print(f"\n{Y}Unesi JSON payload (prazno = {{}}). Završi s Ctrl+D (Linux) ili Ctrl+Z (Win):{RESET}")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        log("Otkazano.", "warn")
        return
    
    raw = '\n'.join(lines).strip()
    if not raw:
        raw = "{}"
    
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        log(f"Nevaljan JSON: {e}", "error")
        return
    
    status, resp = api_call(ep_input, payload)
    print(f"\n{BOLD}{Y}━ ODGOVOR ━{RESET}")
    pretty_print(resp)

# ============================================================
# MAIN MENU
# ============================================================
def main():
    while True:
        banner()
        
        # Pokaži status logina
        if _session_token:
            print(f"  {G}●{RESET} Logiran: {C}{_session_email}{RESET}\n")
        else:
            print(f"  {R}●{RESET} Nisi logiran\n")
        
        print(f"  {BOLD}{Y}[1]{RESET}  👑  King Rank (Max Stats)")
        print(f"  {BOLD}{Y}[2]{RESET}  💰  Max Wallet (999M $/Coins)")
        print(f"  {BOLD}{Y}[3]{RESET}  💵  Dohvati Novac & Coinse")
        print(f"  {BOLD}{Y}[4]{RESET}  🚗  Info o Garaži")
        print(f"  {BOLD}{Y}[5]{RESET}  📋  Dohvati Sva Auta (JSON)")
        print(f"  {BOLD}{Y}[6]{RESET}  👤  Info o Računu")
        print(f"  {BOLD}{Y}[7]{RESET}  🔧  Custom API Poziv")
        print(f"  {BOLD}{R}[8]{RESET}  🗑️  Obriši Račun {R}(OPASNO){RESET}")
        print(f"  {D}[0]{RESET}  🚪  Izlaz\n")
        
        try:
            choice = input(f"{M}[?]{RESET} Odaberi opciju: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Y}Izlaz...{RESET}")
            sys.exit(0)
        
        actions = {
            "1": mod_king_rank,
            "2": mod_max_wallet,
            "3": mod_get_money_coins,
            "4": mod_garage_info,
            "5": mod_get_all_cars,
            "6": mod_account_info,
            "7": mod_custom_call,
            "8": mod_delete_account,
        }
        
        if choice == "0":
            log("Doviđenja!", "ok")
            break
        elif choice in actions:
            try:
                actions[choice]()
            except Exception as e:
                log(f"Greška: {e}", "error")
        else:
            log("Nevažeća opcija!", "error")
        
        print(f"\n{D}─" * 50 + f"{RESET}")
        input(f"{C}[Enter]{RESET} za nastavak...")

if __name__ == "__main__":
    # Provjeri requests
    try:
        import requests
    except ImportError:
        print(f"{R}Greška: 'requests' nije instaliran.{RESET}")
        print(f"{Y}Pokreni: pip install requests{RESET}")
        sys.exit(1)
    
    main()

