import os
import sqlite3
import datetime
import threading
import time
import requests
from flask import Flask
import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8830637060:AAFsUBFtG8YBGzwdy9B5Av65D30T-A3T1-k"

ADMIN_ID = 8671410379

# 4 Force-Join Channels
CHANNELS = [
    {"chat_id": -1003871657552, "name": "Channel 1", "link": "https://t.me/+asPUGy4JXdBiZjU1"},
    {"chat_id": "@Ox1MODS", "name": "OX 1 MODS", "link": "https://t.me/Ox1MODS"},
    {"chat_id": "@Ox2MODS", "name": "OX 2 MODS", "link": "https://t.me/Ox2MODS"},
    {"chat_id": -1003782903063, "name": "OX MODS", "link": "https://t.me/+852hkOgj0UNlZGU9"}
]

# API Endpoints
API_NUMBER_INFO  = "https://api-hub-alpha.vercel.app/api/number-info?key=cybershrfreedemo_9cc8ad86ccdcd8cc53&mobile=9876543210"
API_VEHICLE_INFO = "https://api-hub-alpha.vercel.app/api/vehicle-info?key=cybershrfreedemo_9cc8ad86ccdcd8cc53&number=UP33BH4112"
API_AADHAR_INFO  = "https://api-hub-alpha.vercel.app/api/aadhaar?key=cybershrfreedemo_9cc8ad86ccdcd8cc53&id=123456789012"
API_FAMILY_INFO  = "https://api-hub-alpha.vercel.app/api/family-info?key=cybershrfreedemo_9cc8ad86ccdcd8cc53&aadhar=123456789012"

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
            try:
                bot.send_message(referrer_id, "🎉 <b>Referral Bonus!</b> Someone joined using your link. +5 Credits added.")
            except Exception:
                pass
        conn.commit()
    conn.close()

def deduct_credit(user_id, amount=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

# ----------------- FORCE JOIN VERIFICATION -----------------
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

# ----------------- KEYBOARD MENUS -----------------
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📞 Number to Info"),
        types.KeyboardButton("🚗 Vehicle Info")
    )
    markup.add(
        types.KeyboardButton("🆔 Aadhar to Info"),
        types.KeyboardButton("👨‍👩‍👧 Family Info")
    )
    markup.add(
        types.KeyboardButton("💰 My Balance"),
        types.KeyboardButton("🎁 Refer & Earn")
    )
    markup.add(
        types.KeyboardButton("🎟️ Redeem Code")
    )
    return markup

# ----------------- FLASK KEEP-ALIVE SERVER -----------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running 24/7!"

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
            "⚠️ <b>Access Denied!</b>\n\nYou must join all official channels to use this bot.\nJoin them and tap <b>Check Access</b>.",
            reply_markup=force_join_markup()
        )
        return

    bal = get_user_balance(user_id)
    bot.send_message(
        user_id,
        f"👋 <b>Welcome {message.from_user.first_name}!</b>\n\n"
        f"🎁 <b>Welcome Bonus:</b> 10 Credits added to your account!\n"
        f"💰 <b>Current Balance:</b> {bal} Credits\n\n"
        f"Choose an option below to search:",
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
            f"✅ <b>Access Verified!</b>\n\n"
            f"Your current balance: <b>{bal} Credits</b>\n"
            f"Select any option below to begin:",
            reply_markup=main_menu()
        )
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined all channels yet!", show_alert=True)

# ----------------- ADMIN COMMANDS (/gen & /broadcast) -----------------
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
        bot.reply_to(message, "❌ Credits and uses must be numbers.")
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
            f"🔹 <b>Max Uses:</b> <code>{max_uses} Users</code>"
        )
    except sqlite3.IntegrityError:
        bot.reply_to(message, "❌ This code already exists!")
    finally:
        conn.close()

@bot.message_handler(commands=["broadcast"])
def broadcast_handler(message):
    if message.from_user.id != ADMIN_ID:
        return

    # User can reply to a message with /broadcast OR write /broadcast <text>
    target_msg = message.reply_to_message if message.reply_to_message else None
    broadcast_text = message.text.replace("/broadcast", "").strip()

    if not target_msg and not broadcast_text:
        bot.reply_to(message, "⚠️ <b>Usage:</b>\n1. Type <code>/broadcast Your message here</code>\n2. Or reply to any message/photo with <code>/broadcast</code>.")
        return

    all_users = get_all_users()
    status_msg = bot.send_message(message.chat.id, f"📢 <i>Broadcasting to {len(all_users)} users...</i>")

    success_count = 0
    failed_count = 0

    for uid in all_users:
        try:
            if target_msg:
                bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=target_msg.message_id)
            else:
                bot.send_message(uid, broadcast_text)
            success_count += 1
            time.sleep(0.04)  # Rate limiting protection
        except Exception:
            failed_count += 1

    bot.edit_message_text(
        f"✅ <b>Broadcast Completed!</b>\n\n"
        f"📤 <b>Delivered:</b> {success_count}\n"
        f"❌ <b>Failed / Blocked:</b> {failed_count}",
        chat_id=message.chat.id,
        message_id=status_msg.message_id
    )

# ----------------- USER ACTIONS & SEARCH -----------------
@bot.message_handler(func=lambda msg: True)
def handle_user_actions(message):
    user_id = message.from_user.id

    if not is_user_joined(user_id):
        bot.send_message(
            user_id,
            "⚠️ <b>Access Denied!</b>\n\nYou must join all official channels to use this bot.",
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
            f"Share your referral link with friends and get <b>5 Credits</b> per new join!\n\n"
            f"🔗 <b>Your Link:</b>\n<code>{ref_link}</code>"
        )
        return

    if text == "🎟️ Redeem Code":
        user_states[user_id] = "AWAITING_CODE"
        bot.send_message(user_id, "🎟️ Please enter your Redeem Code:")
        return

    # Menu Selectors
    if text == "📞 Number to Info":
        user_states[user_id] = "SEARCH_NUMBER"
        bot.send_message(user_id, "🔍 <b>Number to Info</b>\n\nSend a 10-digit Indian phone number (without +91):\nExample: <code>9876543210</code>")
        return

    if text == "🚗 Vehicle Info":
        user_states[user_id] = "SEARCH_VEHICLE"
        bot.send_message(user_id, "🚗 <b>Vehicle Info</b>\n\nEnter Vehicle Number:\nExample: <code>UP33BH4112</code>")
        return

    if text == "🆔 Aadhar to Info":
        user_states[user_id] = "SEARCH_AADHAR"
        bot.send_message(user_id, "🆔 <b>Aadhar Info</b>\n\nEnter Aadhaar Number:")
        return

    if text == "👨‍👩‍👧 Family Info":
        user_states[user_id] = "SEARCH_FAMILY"
        bot.send_message(user_id, "👨‍👩‍👧 <b>Family Info</b>\n\nEnter Aadhaar Number for Family details:")
        return

    # Redeem Execution
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
                bot.send_message(user_id, "⚠️ You have already claimed this code!")
            elif times_used >= max_uses:
                bot.send_message(user_id, "❌ Code usage limit exceeded!")
            else:
                cursor.execute("INSERT INTO redeemed_history (code, user_id) VALUES (?, ?)", (code_input, user_id))
                cursor.execute("UPDATE promo_codes SET times_used = times_used + 1 WHERE code = ?", (code_input,))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (credits, user_id))
                conn.commit()
                bot.send_message(user_id, f"🎉 <b>Success!</b>\n\n<b>{credits} Credits</b> added to your account.")
        conn.close()
        user_states.pop(user_id, None)
        return

    # Search Execution
    state = user_states.get(user_id)
    if state in ["SEARCH_NUMBER", "SEARCH_VEHICLE", "SEARCH_AADHAR", "SEARCH_FAMILY"]:
        balance = get_user_balance(user_id)
        if balance < 1:
            bot.send_message(user_id, "❌ <b>Insufficient Balance!</b>\n\nYou need at least 1 credit to search. Use <b>Refer & Earn</b> or redeem a code.")
            user_states.pop(user_id, None)
            return

        query_val = text
        status_msg = bot.send_message(user_id, "⚡ <i>Searching records... Please wait...</i>")

        api_url = ""
        if state == "SEARCH_NUMBER":
            api_url = f"{API_NUMBER_INFO}&mobile={query_val}"
        elif state == "SEARCH_VEHICLE":
            api_url = f"{API_VEHICLE_INFO}&number={query_val}"
        elif state == "SEARCH_AADHAR":
            api_url = f"{API_AADHAR_INFO}&id={query_val}"
        elif state == "SEARCH_FAMILY":
            api_url = f"{API_FAMILY_INFO}&aadhar={query_val}"

        records = []
        try:
            resp = requests.get(api_url, timeout=25)
            res_json = resp.json()

            if isinstance(res_json, dict):
                inner_data = res_json.get("data")
                if isinstance(inner_data, dict):
                    records = inner_data.get("data") or [inner_data]
                elif isinstance(inner_data, list):
                    records = inner_data
                elif "result" in res_json:
                    records = res_json.get("result")
                else:
                    records = [res_json]
            elif isinstance(res_json, list):
                records = res_json
        except Exception as e:
            print("API error:", e)
            records = []

        if not records or (isinstance(records, list) and len(records) == 0):
            bot.edit_message_text("❌ No information was found for this query.", chat_id=user_id, message_id=status_msg.message_id)
            user_states.pop(user_id, None)
            return

        # Deduct 1 credit
        deduct_credit(user_id, 1)
        current_bal = get_user_balance(user_id)

        # Build Clean Text Output (matches screenshot formatting)
        output_blocks = []
        for index, item in enumerate(records, start=1):
            if not isinstance(item, dict):
                continue
            name = item.get("name") or "N/A"
            address = item.get("address") or "N/A"
            aadhaar = item.get("id") or item.get("aadhaar") or item.get("aadhar") or "N/A"
            alt = item.get("alt_number") or item.get("alt") or item.get("alt_mobile") or "N/A"
            circle = item.get("circle") or "N/A"
            father = item.get("father_name") or item.get("father") or "N/A"
            num = item.get("mobile") or item.get("number") or query_val

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

        if not output_blocks:
            bot.edit_message_text("❌ No information was found for this query.", chat_id=user_id, message_id=status_msg.message_id)
            user_states.pop(user_id, None)
            return

        current_time_str = datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")
        result_text = "\n\n".join(output_blocks)
        result_text += (
            f"\n\n📅 GENERATED: {current_time_str}\n"
            f"🛡️ POWERED BY @OxREHANN | @OxRiya1\n\n"
            f"----------------------------------------\n"
            f"TRIES REMAINING: {current_bal}"
        )

        bot.delete_message(user_id, status_msg.message_id)
        # Sent as clean regular text (no full-box monospace)
        bot.send_message(user_id, result_text)
        user_states.pop(user_id, None)

# ----------------- START APPLICATION -----------------
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    print("Bot is successfully running...")
    bot.infinity_polling(skip_pending=True)
                                     
