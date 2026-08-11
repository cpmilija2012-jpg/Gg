#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import sys
import time
from datetime import datetime, timedelta

# ─── CONFIG ───────────────────────────────────
BOT_TOKEN = "8951462015:AAHDQX147lh4Y3a-af5tWR-1W5oPhXiaXTc"
ADMIN_IDS = ["8884756222"]
USERS_FILE = "users.json"

FIREBASE_API_KEY = "AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
FIREBASE_LOGIN_URL = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={FIREBASE_API_KEY}"

ENDPOINTS = {
    "1": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating1",
    "2": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating2",
    "5": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating5",
    "6": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating6",
}

# ─── DATABASE ─────────────────────────────────

def load_db():
    if not os.path.exists(USERS_FILE):
        return {"users": {}, "banned": {}, "admins": []}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(USERS_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_admins():
    db = load_db()
    return list(set(ADMIN_IDS + db.get("admins", [])))

def is_admin(user_id):
    return str(user_id) in get_admins()

def has_access(user_id):
    db = load_db()
    uid = str(user_id)
    if uid in db.get("banned", {}):
        return False, "You are banned from using this bot."
    if uid not in db.get("users", {}):
        return False, "No active subscription. Contact @ILIJASELL to purchase."
    user = db["users"][uid]
    expiry_str = user.get("expiry", "")
    if not expiry_str:
        return False, "No active subscription."
    expiry = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expiry:
        return False, f"Expired on {expiry_str}. Contact @ILIJASELL to renew."
    remaining = expiry - datetime.now()
    return True, f"Active. Expires in {remaining.days} days ({expiry_str})."

# ─── TELEGRAM API ─────────────────────────────

def api(method, payload=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        if payload:
            r = requests.post(url, json=payload, timeout=30)
        else:
            r = requests.get(url, timeout=30)
        return r.json()
    except Exception as e:
        print(f"API error: {e}")
        return {}

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api("sendMessage", payload)

# ─── STATE ────────────────────────────────────

user_states = {}

# ─── KING RANK LOGIC ──────────────────────────

def build_payload():
    rating_data = {k: 100000 for k in [
        "cars", "car_fix", "car_collided", "car_exchange", "car_trade", "car_wash",
        "slicer_cut", "drift_max", "drift", "cargo", "delivery", "taxi", "levels", "gifts",
        "fuel", "offroad", "speed_banner", "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", "push_ups", "burnt_tire", "passanger_distance"
    ]}
    rating_data["time"] = 1000000000
    rating_data["race_win"] = 3000000
    return {"data": json.dumps({"RatingData": rating_data})}

def firebase_login(email, password):
    payload = {
        "clientType": "CLIENT_TYPE_ANDROID",
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(FIREBASE_LOGIN_URL, headers=headers, json=payload, timeout=15)
        data = r.json()
        if r.status_code == 200 and "idToken" in data:
            return data["idToken"], None
        return None, data.get("error", {}).get("message", "Login failed")
    except Exception as e:
        return None, str(e)

def set_rank(token, url):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "okhttp/3.12.13",
    }
    try:
        r = requests.post(url, headers=headers, json=build_payload(), timeout=15)
        if r.status_code == 200:
            return True, None
        try:
            err = r.json()
        except:
            err = r.text[:200]
        return False, err
    except Exception as e:
        return False, str(e)

def process_kingrank(chat_id, email, password):
    send_message(chat_id, "⏳ <b>Connecting to Firebase...</b>")
    token, err = firebase_login(email, password)
    if not token:
        send_message(chat_id, f"❌ <b>Login failed!</b>\n<i>{err}</i>")
        return

    send_message(chat_id, "⏳ <b>Applying King Rank...</b>")
    ok = 0
    results = []
    for key, url in ENDPOINTS.items():
        success, err = set_rank(token, url)
        if success:
            ok += 1
            results.append(f"✅ SetUserRating{key}")
        else:
            results.append(f"❌ SetUserRating{key}: {err}")

    result_text = "\n".join(results)
    if ok == len(ENDPOINTS):
        send_message(chat_id, f"✅ <b>King Rank applied!</b>\n\n{result_text}")
    else:
        send_message(chat_id, f"⚠️ <b>Partially applied</b> ({ok}/{len(ENDPOINTS)})\n\n{result_text}")

    for admin in get_admins():
        send_message(admin, f"📊 <b>King Rank Log</b>\nUser: <code>{chat_id}</code>\nEmail: <code>{email}</code>\nResult: {ok}/{len(ENDPOINTS)}")

# ─── HANDLERS ─────────────────────────────────

def handle_text(chat_id, user_id, text):
    uid = str(user_id)

    # ── Admin Commands ──
    if text.startswith("/panel") and is_admin(user_id):
        markup = {
            "inline_keyboard": [
                [{"text": "➕ Add User", "callback_data": "panel:adduser"}, {"text": "➖ Remove User", "callback_data": "panel:removeuser"}],
                [{"text": "🚫 Ban", "callback_data": "panel:ban"}, {"text": "✅ Unban", "callback_data": "panel:unban"}],
                [{"text": "📋 List Users", "callback_data": "panel:users"}, {"text": "📢 Broadcast", "callback_data": "panel:broadcast"}],
                [{"text": "➕ Add Admin", "callback_data": "panel:addadmin"}]
            ]
        }
        send_message(chat_id, "<b>🔧 Admin Panel</b>\n\nSelect action:", reply_markup=markup)
        return

    if text.startswith("/adduser ") and is_admin(user_id):
        parts = text.split()
        if len(parts) < 3:
            send_message(chat_id, "Usage: /adduser <user_id> <days>")
            return
        target, days = parts[1], parts[2]
        try:
            days = int(days)
        except:
            send_message(chat_id, "Days must be a number.")
            return
        db = load_db()
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        db["users"][target] = {
            "expiry": expiry,
            "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if target in db.get("banned", {}):
            del db["banned"][target]
        save_db(db)
        send_message(chat_id, f"✅ User <code>{target}</code> added.\nExpires: {expiry}")
        send_message(target, f"✅ <b>Access granted!</b>\nDuration: {days} days\nExpires: {expiry}")
        return

    if text.startswith("/removeuser ") and is_admin(user_id):
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, "Usage: /removeuser <user_id>")
            return
        target = parts[1]
        db = load_db()
        if target in db.get("users", {}):
            del db["users"][target]
            save_db(db)
            send_message(chat_id, f"✅ Removed <code>{target}</code>.")
            send_message(target, "❌ Your access was removed.")
        else:
            send_message(chat_id, "User not found.")
        return

    if text.startswith("/ban ") and is_admin(user_id):
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            send_message(chat_id, "Usage: /ban <user_id> [reason]")
            return
        target, reason = parts[1], parts[2] if len(parts) > 2 else "No reason"
        db = load_db()
        db.setdefault("banned", {})[target] = {"reason": reason, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        save_db(db)
        send_message(chat_id, f"🚫 Banned <code>{target}</code>.\nReason: {reason}")
        send_message(target, f"🚫 <b>You are banned.</b>\nReason: {reason}")
        return

    if text.startswith("/unban ") and is_admin(user_id):
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, "Usage: /unban <user_id>")
            return
        target = parts[1]
        db = load_db()
        if target in db.get("banned", {}):
            del db["banned"][target]
            save_db(db)
            send_message(chat_id, f"✅ Unbanned <code>{target}</code>.")
            send_message(target, "✅ <b>You are unbanned.</b>")
        else:
            send_message(chat_id, "Not banned.")
        return

    if text.startswith("/users") and is_admin(user_id):
        db = load_db()
        users = db.get("users", {})
        banned = db.get("banned", {})
        lines = ["<b>👥 Users:</b>"]
        for u, info in users.items():
            b = "🚫" if u in banned else "✅"
            lines.append(f"{b} <code>{u}</code> | {info.get('expiry','N/A')}")
        if banned:
            lines.append("\n<b>🚫 Banned:</b>")
            for u, info in banned.items():
                lines.append(f"<code>{u}</code> | {info.get('reason','')}")
        send_message(chat_id, "\n".join(lines)[:4000])
        return

    if text.startswith("/broadcast ") and is_admin(user_id):
        msg = text[len("/broadcast "):]
        db = load_db()
        sent = 0
        for uid in db.get("users", {}):
            try:
                send_message(uid, f"📢 <b>Announcement</b>\n\n{msg}")
                sent += 1
                time.sleep(0.05)
            except:
                pass
        send_message(chat_id, f"📢 Sent to {sent} users.")
        return

    if text.startswith("/addadmin ") and is_admin(user_id):
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, "Usage: /addadmin <user_id>")
            return
        target = parts[1]
        db = load_db()
        if target not in db.get("admins", []):
            db.setdefault("admins", []).append(target)
            save_db(db)
            send_message(chat_id, f"✅ Admin <code>{target}</code> added.")
        else:
            send_message(chat_id, "Already admin.")
        return

    # ── User Commands ──
    if text == "/start":
        active, msg = has_access(user_id)
        send_message(chat_id,
            f"👋 <b>CPM King Rank Service</b>\n\n"
            f"🆔 <b>Your ID:</b> <code>{user_id}</code>\n"
            f"📸 Instagram: <b>ilija.jvcc</b>\n"
            f"📱 Telegram: <b>@ILIJASELL</b>\n\n"
            f"📋 <b>Status:</b> {msg}\n\n"
            f"Use /kingrank to start."
        )
        return

    if text == "/status":
        active, msg = has_access(user_id)
        icon = "✅" if active else "❌"
        send_message(chat_id, f"{icon} <b>Status:</b>\n{msg}")
        return

    if text == "/kingrank":
        active, msg = has_access(user_id)
        if not active:
            send_message(chat_id, f"❌ <b>Access Denied</b>\n{msg}")
            return
        user_states[chat_id] = {"action": "await_email"}
        send_message(chat_id, "📧 <b>Enter CPM Email:</b>")
        return

    # ── State Machine ──
    state = user_states.get(chat_id)
    if state:
        action = state["action"]
        if action == "await_email":
            user_states[chat_id] = {"action": "await_password", "email": text.strip()}
            send_message(chat_id, "🔑 <b>Enter CPM Password:</b>")
            return
        elif action == "await_password":
            email = state["email"]
            password = text.strip()
            del user_states[chat_id]
            process_kingrank(chat_id, email, password)
            return

    send_message(chat_id, "❓ Unknown command. Use /start")

def handle_callback(chat_id, user_id, data):
    if not is_admin(user_id):
        return
    action = data.replace("panel:", "")
    cmds = {
        "adduser": "➕ <b>Add User</b>\n<code>/adduser user_id days</code>",
        "removeuser": "➖ <b>Remove User</b>\n<code>/removeuser user_id</code>",
        "ban": "🚫 <b>Ban User</b>\n<code>/ban user_id reason</code>",
        "unban": "✅ <b>Unban User</b>\n<code>/unban user_id</code>",
        "users": None,
        "broadcast": "📢 <b>Broadcast</b>\n<code>/broadcast message</code>",
        "addadmin": "➕ <b>Add Admin</b>\n<code>/addadmin user_id</code>",
    }
    if action == "users":
        handle_text(chat_id, user_id, "/users")
    elif action in cmds:
        send_message(chat_id, cmds[action])

# ─── MAIN LOOP ────────────────────────────────

def main():
    print("🤖 Bot started. Press Ctrl+C to stop.")
    offset = 0
    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": offset, "limit": 100},
                timeout=60
            )
            data = r.json()
            if not data.get("ok"):
                time.sleep(5)
                continue

            for upd in data.get("result", []):
                offset = upd["update_id"] + 1

                if "message" in upd:
                    m = upd["message"]
                    handle_text(m["chat"]["id"], m["from"]["id"], m.get("text", ""))

                elif "callback_query" in upd:
                    cq = upd["callback_query"]
                    handle_callback(cq["message"]["chat"]["id"], cq["from"]["id"], cq.get("data", ""))
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                                  json={"callback_query_id": cq["id"]})

        except KeyboardInterrupt:
            print("\n🛑 Stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
