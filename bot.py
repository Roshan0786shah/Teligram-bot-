import telebot
import re
import time
import threading
import random
from datetime import datetime, timedelta
from telebot.types import ChatPermissions
from flask import Flask

# =====================
# SERVER STATUS SYSTEM
# =====================
app = Flask('')

@app.route('/')
def home():
    return "Cyber SHR Shield - System Online"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# =====================
# CONFIG
# =====================
BOT_TOKEN = "8372879804:AAEKowoa_EaSy6TeA1aoT9jUNEm1pEeLXe8"

FORBIDDEN_WORDS = ["dm me", "inbox", "inbox me", "pm me"]
MAX_WARNINGS = 3
AUTO_DELETE_SEC = 0
FOOTER = "\n\nTHANK YOU TEAM CYBER SHR☠️"

MUTE_MINUTES = 30
YOUTUBE_REGEX = re.compile(r"(youtube\.com|youtu\.be)", re.I)
LINK_REGEX = re.compile(r"https?://\S+", re.I)

bot = telebot.TeleBot(BOT_TOKEN)
warnings = {}  
captcha_users = {}

# =====================
# UTIL FUNCTIONS
# =====================
def is_admin(chat_id, user_id):
    try:
        return any(a.user.id == user_id for a in bot.get_chat_administrators(chat_id))
    except:
        return False

def get_username(u):
    return f"@{u.username}" if u.username else (u.first_name or "User")

def mute_user(chat_id, user_id):
    until = datetime.now() + timedelta(minutes=MUTE_MINUTES)
    bot.restrict_chat_member(
        chat_id, user_id, until_date=until,
        permissions=ChatPermissions(can_send_messages=False)
    )

def unmute_user(chat_id, user_id):
    bot.restrict_chat_member(
        chat_id, user_id,
        permissions=ChatPermissions(
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True
        )
    )

def warn_user(chat_id, user_id, user_obj, reason):
    key = (chat_id, user_id)
    warnings[key] = warnings.get(key, 0) + 1
    wc = warnings[key]
    uname = get_username(user_obj)

    if wc < MAX_WARNINGS:
        mute_user(chat_id, user_id)
        bot.send_message(
            chat_id,
            f"⚠️ WARNING {wc}/{MAX_WARNINGS}\n👤 User: {uname}\n🚫 Reason: {reason}\n"
            f"🔇 Muted for {MUTE_MINUTES} minutes" + FOOTER
        )
    else:
        bot.kick_chat_member(chat_id, user_id)
        bot.send_message(
            chat_id, 
            f"❌ USER KICKED\n👤 User: {uname}\n📛 Reason: Reached {MAX_WARNINGS} warnings" + FOOTER
        )
        warnings.pop(key, None)

# =====================
# WELCOME & CAPTCHA
# =====================
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    chat_id = message.chat.id
    for user in message.new_chat_members:
        if user.is_bot: continue
        
        username = get_username(user)
        a, b = random.randint(1, 9), random.randint(1, 9)
        captcha_users[user.id] = a + b
        
        mute_user(chat_id, user.id)
        bot.send_message(
            chat_id,
            f"👋 Welcome {username}\n🔥 Welcome to CYBER SHR Group\n\n"
            f"🧮 **Verify yourself**\nSolve: `{a} + {b} = ?`\nType: `/verify (answer)`" + FOOTER,
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['verify'])
def verify_user(message):
    user_id = message.from_user.id
    if user_id not in captcha_users:
        bot.reply_to(message, "ℹ️ You are already verified.")
        return
    try:
        ans = int(message.text.split()[1])
        if ans == captcha_users[user_id]:
            unmute_user(message.chat.id, user_id)
            del captcha_users[user_id]
            bot.reply_to(message, "✅ Verification successful!")
        else:
            bot.reply_to(message, "❌ Wrong answer! Try again.")
    except:
        bot.reply_to(message, "❌ Use format: /verify 10")

# =====================
# AUTO MODERATION
# =====================
@bot.message_handler(func=lambda m: True, content_types=["text"])
def auto_moderation(m):
    if is_admin(m.chat.id, m.from_user.id): return
    
    text = m.text.lower()
    reason = None
    for w in FORBIDDEN_WORDS:
        if w in text: 
            reason = "DM / Inbox not allowed"
            break
    
    if LINK_REGEX.search(text) and not YOUTUBE_REGEX.search(text):
        reason = "Only YouTube links allowed"

    if reason:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass
        warn_user(m.chat.id, m.from_user.id, m.from_user, reason)

# =====================
# ADMIN COMMANDS
# =====================
@bot.message_handler(commands=["unmute"])
def cmd_unmute(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if m.reply_to_message:
        unmute_user(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "✅ User Unmuted")
    else:
        bot.reply_to(m, "❗ Reply to user's message to unmute.")

@bot.message_handler(commands=["resetwarn"])
def cmd_reset(m):
    if not is_admin(m.chat.id, m.from_user.id) or not m.reply_to_message: return
    warnings.pop((m.chat.id, m.reply_to_message.from_user.id), None)
    bot.reply_to(m, f"✅ Warnings reset" + FOOTER)

@bot.message_handler(commands=["rules"])
def rules(m):
    bot.reply_to(
        m, 
        "📜 𝗚𝗥𝗢𝗨𝗣 𝗥𝗨𝗟𝗘𝗦📢\n1️⃣ No Spam\n2️⃣ No DM/Inbox\n3️⃣ No Selling/Promo\n"
        "4️⃣ YouTube Links Only\n5️⃣ 3 Warnings = Kick" + FOOTER
    )

# =====================
# RUN BOT
# =====================
if __name__ == "__main__":
    keep_alive()
    print("🚨 Cyber SHR Shield Bot Running...")
    bot.infinity_polling()
    
