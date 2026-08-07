#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║           CPM2 TERMUX TOOL v3.0                              ║
║  Add Money (50M) | Add Coins (300K) | King Rank | Cars      ║
║  Change Email | Change Password                              ║
╚══════════════════════════════════════════════════════════════╝
"""

import requests
import json
import os
import sys

# ============================================================
# CONFIG
# ============================================================
API_KEY = 'AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ'
BASE_URL = 'https://europe-west1-cpm-2-7cea1.cloudfunctions.net'
FIREBASE_LOGIN = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={API_KEY}"

# Boje
G = '\033[92m'; Y = '\033[93m'; C = '\033[96m'; R = '\033[91m'
M = '\033[95m'; W = '\033[97m'; D = '\033[90m'; RESET = '\033[0m'; BOLD = '\033[1m'

_session = None
_uid = None
_email = None

# ============================================================
# POMOĆNE FUNKCIJE
# ============================================================
def clear():
    os.system('clear' if os.name != 'nt' else 'cls')

def banner():
    clear()
    print(f"""{C}
    ╔══════════════════════════════════════════════════╗
    ║   {W}CPM2 TERMUX TOOL v3.0{C}                        ║
    ║   {Y}Money • Coins • Rank • Cars • Account{C}        ║
    ╚══════════════════════════════════════════════════╝{RESET}""")

def log(msg, t="info"):
    p = {"info": f"{C}[*]{RESET}", "ok": f"{G}[✓]{RESET}",
         "warn": f"{Y}[!]{RESET}", "error": f"{R}[✗]{RESET}",
         "input": f"{M}[?]{RESET}"}.get(t, f"{C}[*]{RESET}")
    print(f"{p} {msg}")

def pretty(data):
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(str(data)[:800])

def firebase_login(email, password):
    payload = {
        "clientType": "CLIENT_TYPE_ANDROID",
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; CPM2)",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(FIREBASE_LOGIN, headers=headers, json=payload, timeout=30)
        d = r.json()
        if r.status_code == 200 and 'idToken' in d:
            return d['idToken'], d.get('localId')
        err = d.get('error', {}).get('message', 'Unknown error')
        log(f"Firebase: {err}", "error")
        return None, None
    except Exception as e:
        log(f"Network error: {e}", "error")
        return None, None

def call(endpoint, data=None, use_token=True):
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "okhttp/4.12.0",
        "x-api-key": API_KEY
    }
    payload = data.copy() if data else {}
    
    if use_token and _session:
        headers["Authorization"] = f"Bearer {_session}"
        payload["idToken"] = _session
        if _uid and "localId" not in payload and "userId" not in payload:
            payload["localId"] = _uid
    
    try:
        log(f"Calling {Y}{endpoint}{RESET}...", "info")
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            log(f"Status {G}{r.status_code}{RESET}", "ok")
        else:
            log(f"Status {R}{r.status_code}{RESET}", "error")
        try:
            return r.status_code, r.json()
        except:
            return r.status_code, r.text[:500]
    except Exception as e:
        log(f"Error: {e}", "error")
        return 0, str(e)

def ensure_login():
    global _session, _uid, _email
    if _session:
        return True
    log("Login required", "warn")
    em = input(f"{M}[?]{RESET} Email: ").strip()
    pw = input(f"{M}[?]{RESET} Password: ").strip()
    if not em or not pw:
        return False
    token, uid = firebase_login(em, pw)
    if token:
        _session = token
        _uid = uid
        _email = em
        log(f"Logged in: {C}{em}{RESET}", "ok")
        return True
    return False

# ============================================================
# FUNKCIJE
# ============================================================

def add_money():
    if not ensure_login(): return
    print(f"\n{BOLD}{Y}━━ ADD MONEY (Max 50,000,000) ━━{RESET}")
    try:
        amt = int(input(f"{M}[?]{RESET} Amount: ").strip().replace(",", ""))
        if not 1 <= amt <= 50000000:
            log("Must be 1 - 50,000,000", "error"); return
    except ValueError:
        log("Invalid number", "error"); return
    
    # Format 1: wrapped data string (CPM1 style)
    payload1 = {"data": json.dumps({"Money": amt})}
    s, r = call("SaveWalletData23_1", payload1)
    if s == 200:
        log(f"Money set to {G}{amt:,}${RESET}", "ok"); return
    
    # Format 2: direct JSON
    log("Retrying with direct format...", "warn")
    s2, r2 = call("SaveWalletData23_1", {"Money": amt})
    if s2 == 200:
        log(f"Money set to {G}{amt:,}${RESET}", "ok"); return
    
    log("Failed!", "error"); pretty(r if s != 200 else r2)

def add_coins():
    if not ensure_login(): return
    print(f"\n{BOLD}{Y}━━ ADD COINS (Max 300,000) ━━{RESET}")
    try:
        amt = int(input(f"{M}[?]{RESET} Amount: ").strip().replace(",", ""))
        if not 1 <= amt <= 300000:
            log("Must be 1 - 300,000", "error"); return
    except ValueError:
        log("Invalid number", "error"); return
    
    payload1 = {"data": json.dumps({"Coins": amt})}
    s, r = call("SaveWalletData23_1", payload1)
    if s == 200:
        log(f"Coins set to {G}{amt:,}{RESET}", "ok"); return
    
    log("Retrying direct format...", "warn")
    s2, r2 = call("SaveWalletData23_1", {"Coins": amt})
    if s2 == 200:
        log(f"Coins set to {G}{amt:,}{RESET}", "ok"); return
    
    log("Failed!", "error"); pretty(r if s != 200 else r2)

def king_rank():
    if not ensure_login(): return
    print(f"\n{BOLD}{Y}━━ KING RANK ━━{RESET}")
    log("SetUserRating23_1 is DEAD (404)", "warn")
    log("Trying ValidateRank23_1...", "info")
    
    rating = {
        "cars": 100000, "car_fix": 100000, "car_collided": 100000,
        "car_exchange": 100000, "car_trade": 100000, "car_wash": 100000,
        "slicer_cut": 100000, "drift_max": 100000, "drift": 100000,
        "cargo": 100000, "delivery": 100000, "taxi": 100000,
        "levels": 100000, "gifts": 100000, "fuel": 100000,
        "offroad": 100000, "speed_banner": 100000, "reactions": 100000,
        "police": 100000, "run": 100000, "real_estate": 100000,
        "t_distance": 100000, "treasure": 100000, "block_post": 100000,
        "push_ups": 100000, "burnt_tire": 100000, "passanger_distance": 100000,
        "time": 999999999, "race_win": 9999, "race_lose": 0, "rating": 1000000
    }
    
    # Pokušaj 1: wrapped data
    s1, r1 = call("ValidateRank23_1", {"data": json.dumps({"RatingData": rating})})
    if s1 == 200:
        log("King Rank applied!", "ok"); pretty(r1); return
    pretty(r1)
    
    # Pokušaj 2: direktno
    log("Trying direct format...", "warn")
    s2, r2 = call("ValidateRank23_1", {"RatingData": rating})
    if s2 == 200:
        log("King Rank applied!", "ok"); return
    pretty(r2)
    
    # Pokušaj 3: 22_1 alternativa ako postoji
    log("Trying 22_1 endpoint...", "warn")
    s3, r3 = call("SetUserRating22_1", {"data": json.dumps({"RatingData": rating})}, use_token=True)
    if s3 == 200:
        log("King Rank applied via 22_1!", "ok"); return
    log("All rank methods failed.", "error")

def unlock_car():
    if not ensure_login(): return
    print(f"\n{BOLD}{Y}━━ UNLOCK CAR BY ID ━━{RESET}")
    cid = input(f"{M}[?]{RESET} Car ID: ").strip()
    if not cid:
        return
    
    # Pokušaj 1: SaveCar23_1
    log("Trying SaveCar23_1...", "info")
    car_data = {"carId": cid, "owned": True, "unlocked": True}
    s1, r1 = call("SaveCar23_1", {"data": json.dumps(car_data)})
    if s1 == 200:
        log(f"Car {C}{cid}{RESET} unlocked!", "ok"); return
    pretty(r1)
    
    # Pokušaj 2: BuyCar23_1 (free)
    log("Trying BuyCar23_1...", "info")
    s2, r2 = call("BuyCar23_1", {"data": json.dumps({"carId": cid, "price": 0})})
    if s2 == 200:
        log(f"Car {C}{cid}{RESET} added!", "ok"); return
    pretty(r2)
    
    log("Failed to unlock car.", "error")

def change_email():
    if not ensure_login(): return
    print(f"\n{BOLD}{Y}━━ CHANGE EMAIL ━━{RESET}")
    new_em = input(f"{M}[?]{RESET} New email: ").strip()
    if not new_em or "@" not in new_em:
        log("Invalid email", "error"); return
    
    # Pokušaj 1: wrapped
    s1, r1 = call("ChangeEmailAndPassword23_1", {
        "data": json.dumps({"email": new_em, "idToken": _session})
    })
    if s1 == 200:
        log(f"Email changed to {C}{new_em}{RESET}", "ok"); return
    pretty(r1)
    
    # Pokušaj 2: direktno
    log("Trying direct format...", "warn")
    s2, r2 = call("ChangeEmailAndPassword23_1", {
        "email": new_em,
        "idToken": _session,
        "localId": _uid
    })
    if s2 == 200:
        log(f"Email changed!", "ok"); return
    pretty(r2)
    log("Failed.", "error")

def change_password():
    if not ensure_login(): return
    print(f"\n{BOLD}{Y}━━ CHANGE PASSWORD ━━{RESET}")
    new_pw = input(f"{M}[?]{RESET} New password: ").strip()
    if len(new_pw) < 6:
        log("Min 6 chars", "error"); return
    
    # Pokušaj 1: wrapped
    s1, r1 = call("ChangeEmailAndPassword23_1", {
        "data": json.dumps({"password": new_pw, "idToken": _session})
    })
    if s1 == 200:
        log("Password changed!", "ok"); return
    pretty(r1)
    
    # Pokušaj 2: direktno
    log("Trying direct format...", "warn")
    s2, r2 = call("ChangeEmailAndPassword23_1", {
        "password": new_pw,
        "idToken": _session,
        "localId": _uid
    })
    if s2 == 200:
        log("Password changed!", "ok"); return
    pretty(r2)
    log("Failed.", "error")

def check_wallet():
    if not ensure_login(): return
    print(f"\n{BOLD}{Y}━━ CURRENT WALLET ━━{RESET}")
    s1, r1 = call("GetMoney23_1", {})
    s2, r2 = call("GetCoins23_1", {})
    print(f"{C}Money:{RESET}"); pretty(r1)
    print(f"{C}Coins:{RESET}"); pretty(r2)

# ============================================================
# MAIN
# ============================================================
def main():
    while True:
        banner()
        status = f"{G}● Logged in: {C}{_email}{RESET}" if _session else f"{R}● Not logged in{RESET}"
        print(f"    {status}\n")
        
        print(f"    {BOLD}{Y}[1]{RESET} 💰 Add Money (Max 50M)")
        print(f"    {BOLD}{Y}[2]{RESET} 🪙 Add Coins (Max 300K)")
        print(f"    {BOLD}{Y}[3]{RESET} 👑 King Rank")
        print(f"    {BOLD}{Y}[4]{RESET} 🚗 Unlock Car by ID")
        print(f"    {BOLD}{Y}[5]{RESET} 📧 Change Email")
        print(f"    {BOLD}{Y}[6]{RESET} 🔑 Change Password")
        print(f"    {BOLD}{C}[7]{RESET} 👁  Check Wallet")
        print(f"    {D}[0]{RESET} 🚪 Exit\n")
        
        try:
            c = input(f"{M}[?]{RESET} Select: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        
        actions = {
            "1": add_money, "2": add_coins, "3": king_rank,
            "4": unlock_car, "5": change_email, "6": change_password,
            "7": check_wallet
        }
        
        if c == "0":
            log("Goodbye!", "ok"); break
        elif c in actions:
            try:
                actions[c]()
            except Exception as e:
                log(f"Error: {e}", "error")
        else:
            log("Invalid option", "error")
        
        input(f"\n{C}[Enter]{RESET} to continue...")

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print(f"{R}Install requests: pip install requests{RESET}")
        sys.exit(1)
    main()
