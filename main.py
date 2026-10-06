import os
import sqlite3
import datetime
import threading
import requests
from flask import Flask
import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "⚠️⚠️⚠️⚠️⚠️⚠️ BOT TOKEN"

# 4 Force-Join Channels configuration
CHANNELS = [
    {"chat_id": -1003871657552, "name": "Channel 1", "link": "https://t.me/+asPUGy4JXdBiZjU1"},
    {"chat_id": "@Ox1MODS", "name": "OX 1 MODS", "link": "https://t.me/Ox1MODS"},
    {"chat_id": "@Ox2MODS", "name": "OX 2 MODS", "link": "https://t.me/Ox2MODS"},
    {"chat_id": -1003782903063, "name": "OX MODS", "link": "https://t.me/+852hkOgj0UNlZGU9"}
]

ADMIN_ID = 8671410379

# API Endpoints
API_NUMBER_INFO  = "⚠️⚠️⚠️⚠️⚠️⚠️ API 1 (Number to Info)"
API_VEHICLE_INFO = "⚠️⚠️⚠️⚠️⚠️⚠️ API 2 (Vehicle Info)"
API_AADHAR_INFO  = "⚠️⚠️⚠️⚠️⚠️⚠️ API 3 (Aadhar to Info)"
API_TG_INFO      = "⚠️⚠️⚠️⚠️⚠️⚠️ API 4 (TG to Number)"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ----------------- DATABASE SETUP -----------------
def init_db():
    conn = sqlite3.connect("bot_database.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 10,
            referred_by INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            credits INTEGER,
            max_uses INTEGER,
            times_used INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS redeemed_history (
            code TEXT,
            user_id INTEGER,
            PRIMARY KEY (code, user_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("bot_database.db", check_same_thread=False)

def get_user_balance(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def register_user(user_id, referrer_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, balance, referred_by) VALUES (?, 10, ?)", (user_id, referrer_id))
        if referrer_id and referrer_id != user_id:
            cursor.execute("UPDATE users SET balance = balance + 5 WHERE user_id = ?", (referrer_id,))
        conn.commit()
    conn.close()

def deduct_credit(user_id, amount=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def add_user_credit(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# ----------------- FORCE JOIN CHECK -----------------
def is_user_joined(user_id):
    if user_id == ADMIN_ID:
        return True
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch["chat_id"], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception:
            return False
    return True

def force_join_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=ch["name"], url=ch["link"]) for ch in CHANNELS]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton(text="✅ Check Access", callback_data="verify_join"))
    return markup

# ----------------- KEYBOARDS -----------------
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📞 Number to Info"),
        types.KeyboardButton("🚗 Vehicle Info")
    )
    markup.add(
        types.KeyboardButton("🆔 Aadhar to Info"),
        types.KeyboardButton("✈️ TG to Number")
    )
    markup.add(
        types.KeyboardButton("💰 My Balance"),
        types.KeyboardButton("🎁 Refer & Earn")
    )
    markup.add(
        types.KeyboardButton("🎟️ Redeem Code")
    )
    return markup

# ----------------- RENDER KEEP-ALIVE SERVER -----------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running healthy 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ----------------- BOT HANDLERS -----------------
user_states = {}

@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    register_user(user_id, referrer)

    if not is_user_joined(user_id):
        bot.send_message(
            user_id,
            "⚠️ <b>Access Denied!</b>\n\nYou must join all our official channels to use this bot. Click the buttons below to join, then tap <b>Check Access</b>.",
            reply_markup=force_join_markup()
        )
        return

    bal = get_user_balance(user_id)
    bot.send_message(
        user_id,
        f"👋 <b>Welcome {message.from_user.first_name}!</b>\n\n"
        f"🎁 <b>Welcome Bonus:</b> 10 Credits added to your wallet!\n"
        f"💰 <b>Current Balance:</b> {bal} Credits\n\n"
        f"Select any option below to begin searching:",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def handle_verification(call):
    user_id = call.from_user.id
    if is_user_joined(user_id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bal = get_user_balance(user_id)
        bot.send_message(
            user_id,
            f"✅ <b>Access Approved!</b>\n\n"
            f"Your current balance: <b>{bal} Credits</b>\n"
            f"Use the menu below to search:",
            reply_markup=main_menu()
        )
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined all channels yet!", show_alert=True)

# ----------------- ADMIN COMMANDS -----------------
@bot.message_handler(commands=["gen"])
def generate_code_handler(message):
    if message.from_user.id != ADMIN_ID:
        return

    # Syntax: /gen <code> <credits> <max_uses>
    parts = message.text.split()
    if len(parts) != 4:
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/gen &lt;code&gt; &lt;credits&gt; &lt;max_uses&gt;</code>\nExample: <code>/gen Ox1Rt5 500 5</code>")
        return

    code = parts[1]
    try:
        credits = int(parts[2])
        max_uses = int(parts[3])
    except ValueError:
        bot.reply_to(message, "❌ Credits aur max uses number format me hone chahiye.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO promo_codes (code, credits, max_uses, times_used) VALUES (?, ?, ?, 0)",
                       (code, credits, max_uses))
        conn.commit()
        bot.send_message(
            message.chat.id,
            f"🎟️ <b>Gift Code Created!</b>\n\n"
            f"🔹 <b>Code:</b> <code>{code}</code>\n"
            f"🔹 <b>Reward:</b> <code>{credits} Credits</code>\n"
            f"🔹 <b>Max Limit:</b> <code>{max_uses} Users</code>"
        )
    except sqlite3.IntegrityError:
        bot.reply_to(message, "❌ Yeh code pehle se exist karta hai!")
    finally:
        conn.close()

# ----------------- USER INTERACTIONS -----------------
@bot.message_handler(func=lambda msg: True)
def handle_menu_and_inputs(message):
    user_id = message.from_user.id

    if not is_user_joined(user_id):
        bot.send_message(
            user_id,
            "⚠️ <b>Access Denied!</b>\n\nYou must join all our official channels to use this service.",
            reply_markup=force_join_markup()
        )
        return

    text = message.text.strip()

    if text == "💰 My Balance":
        bal = get_user_balance(user_id)
        bot.send_message(user_id, f"💳 <b>Your Account Details</b>\n\nUser ID: <code>{user_id}</code>\nBalance: <b>{bal} Credits</b>\nCost per search: <b>1 Credit</b>")
        return

    if text == "🎁 Refer & Earn":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(
            user_id,
            f"🎁 <b>Refer & Earn Program</b>\n\n"
            f"Share your referral link with your friends and earn <b>5 Credits</b> per user join!\n\n"
            f"🔗 <b>Your Link:</b>\n<code>{ref_link}</code>"
        )
        return

    if text == "🎟️ Redeem Code":
        user_states[user_id] = "AWAITING_CODE"
        bot.send_message(user_id, "🎟️ Please enter your Redeem Code:")
        return

    # Handle Service Selectors
    if text == "📞 Number to Info":
        user_states[user_id] = "SEARCH_NUMBER"
        bot.send_message(user_id, "🔍 <b>Number to Info</b>\n\nSend a 10-digit Indian mobile number (without +91):\nExample: <code>9876543210</code>")
        return

    if text == "🚗 Vehicle Info":
        user_states[user_id] = "SEARCH_VEHICLE"
        bot.send_message(user_id, "🚗 <b>Vehicle Info</b>\n\nEnter vehicle RC registration number:\nExample: <code>UP52AB1234</code>")
        return

    if text == "🆔 Aadhar to Info":
        user_states[user_id] = "SEARCH_AADHAR"
        bot.send_message(user_id, "🆔 <b>Aadhar Info</b>\n\nEnter 12-digit Aadhaar Number:\nExample: <code>222149609562</code>")
        return

    if text == "✈️ TG to Number":
        user_states[user_id] = "SEARCH_TG"
        bot.send_message(user_id, "✈️ <b>TG to Number</b>\n\nEnter Telegram User ID or Username:")
        return

    # Redeem State Processing
    if user_states.get(user_id) == "AWAITING_CODE":
        code_input = text
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT credits, max_uses, times_used FROM promo_codes WHERE code = ?", (code_input,))
        code_data = cursor.fetchone()

        if not code_data:
            bot.send_message(user_id, "❌ Invalid Redeem Code!")
        else:
            credits, max_uses, times_used = code_data
            cursor.execute("SELECT 1 FROM redeemed_history WHERE code = ? AND user_id = ?", (code_input, user_id))
            if cursor.fetchone():
                bot.send_message(user_id, "⚠️ You have already redeemed this code!")
            elif times_used >= max_uses:
                bot.send_message(user_id, "❌ This code has reached its maximum usage limit!")
            else:
                cursor.execute("INSERT INTO redeemed_history (code, user_id) VALUES (?, ?)", (code_input, user_id))
                cursor.execute("UPDATE promo_codes SET times_used = times_used + 1 WHERE code = ?", (code_input,))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (credits, user_id))
                conn.commit()
                bot.send_message(user_id, f"🎉 <b>Success!</b>\n\n<b>{credits} Credits</b> have been added to your balance.")
        conn.close()
        user_states.pop(user_id, None)
        return

    # Search Execution
    state = user_states.get(user_id)
    if state in ["SEARCH_NUMBER", "SEARCH_VEHICLE", "SEARCH_AADHAR", "SEARCH_TG"]:
        balance = get_user_balance(user_id)
        if balance < 1:
            bot.send_message(user_id, "❌ <b>Insufficient Balance!</b>\n\nYou need at least 1 credit to perform a search. Use <b>Refer & Earn</b> or redeem a code to get credits.")
            user_states.pop(user_id, None)
            return

        query_value = text
        status_msg = bot.send_message(user_id, "⚡ <i>Processing your search... Please wait...</i>")

        # Map correct API
        api_url = ""
        if state == "SEARCH_NUMBER":
            api_url = f"{API_NUMBER_INFO}?num={query_value}"
        elif state == "SEARCH_VEHICLE":
            api_url = f"{API_VEHICLE_INFO}?rc={query_value}"
        elif state == "SEARCH_AADHAR":
            api_url = f"{API_AADHAR_INFO}?uid={query_value}"
        elif state == "SEARCH_TG":
            api_url = f"{API_TG_INFO}?tgid={query_value}"

        records = []
        try:
            resp = requests.get(api_url, timeout=20)
            data = resp.json()

            # Normalize data into list of records
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = data.get("records") or data.get("result") or [data]
        except Exception:
            records = []

        if not records:
            bot.edit_message_text("❌ No information was found for this query.", chat_id=user_id, message_id=status_msg.message_id)
            user_states.pop(user_id, None)
            return

        # Deduct 1 credit
        deduct_credit(user_id, 1)
        current_bal = get_user_balance(user_id)

        # Build Card Output
        output_blocks = []
        for index, item in enumerate(records, start=1):
            name = item.get("name", "N/A")
            address = item.get("address", "N/A")
            aadhaar = item.get("aadhaar") or item.get("aadhar", "N/A")
            alt = item.get("alt") or item.get("alt_mobile", "N/A")
            circle = item.get("circle", "N/A")
            father = item.get("father") or item.get("father_name", "N/A")
            num = item.get("num") or item.get("mobile", query_value)

            block = (
                f"[ RECORD {index} ]\n"
                f"👤 NAME: {name}\n"
                f"🏠 ADDRESS: {address}\n"
                f"🆔 AADHAAR: {aadhaar}\n"
                f"📱 ALT: {alt}\n"
                f"🔵 CIRCLE: {circle}\n"
                f"👨 FATHER: {father}\n"
                f"🔷 Num: {num}\n"
                f"----------------------------------------"
            )
            output_blocks.append(block)

        current_time_str = datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")
        result_text = "\n\n".join(output_blocks)
        result_text += (
            f"\n\n📅 GENERATED: {current_time_str}\n"
            f"🛡️ POWERED BY @OxREHANN | @OxRiya1\n\n"
            f"----------------------------------------\n"
            f"TRIES REMAINING: {current_bal}"
        )

        bot.delete_message(user_id, status_msg.message_id)
        bot.send_message(user_id, f"<code>{result_text}</code>", parse_mode="HTML")
        user_states.pop(user_id, None)

# ----------------- START APPLICATION -----------------
if __name__ == "__main__":
    # Start web keep-alive server in background
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    print("Bot is starting polling...")
    bot.infinity_polling(skip_pending=True)
