import os
import requests
import logging
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================== CONFIG ==================
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
OPENAI_KEY = os.getenv("OPENAI_KEY")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN missing")

# ================== KEEP ALIVE ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "Ultra AI Bot Running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run).start()

# ================== MEMORY ==================
user_memory = {}

def get_memory(uid):
    if uid not in user_memory:
        user_memory[uid] = []
    return user_memory[uid]

def add_memory(uid, role, text):
    mem = get_memory(uid)
    mem.append({"role": role, "text": text})
    if len(mem) > 10:
        mem.pop(0)

# ================== GEMINI ==================
def ask_gemini(text):
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

        r = requests.post(url, json={
            "contents": [{"parts": [{"text": text}]}]
        }, timeout=20)

        data = r.json()

        if "error" in data:
            return None

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except:
        return None

# ================== GPT ==================
def ask_gpt(text):
    try:
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": text}]
        }

        r = requests.post(url, json=payload, headers=headers, timeout=20)
        data = r.json()

        return data["choices"][0]["message"]["content"]

    except:
        return None

# ================== AI ENGINE ==================
def ai_engine(uid, text):

    history = get_memory(uid)
    context = "\n".join([f"{m['role']}: {m['text']}" for m in history])

    prompt = f"""
شما یک AI هوشمند هستی.

تاریخ گفتگو:
{context}

کاربر:
{text}
"""

    # 1. Gemini
    res = ask_gemini(prompt)
    if res:
        add_memory(uid, "user", text)
        add_memory(uid, "ai", res)
        return "🧠 Gemini:\n\n" + res

    # 2. GPT
    res = ask_gpt(prompt)
    if res:
        add_memory(uid, "user", text)
        add_memory(uid, "ai", res)
        return "🤖 GPT:\n\n" + res

    # 3. fallback
    return "⚠️ AI در دسترس نیست، بعداً تلاش کنید."

# ================== MENU ==================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 چت AI", callback_data="chat")],
        [InlineKeyboardButton("📚 کمک درسی", callback_data="study")],
        [InlineKeyboardButton("🧠 خلاصه ساز", callback_data="summary")]
    ])

# ================== MODE ==================
user_mode = {}

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Ultra Pro AI Bot\nیک حالت انتخاب کن:",
        reply_markup=menu()
    )

# ================== BUTTONS ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if q.data == "chat":
        user_mode[uid] = "chat"
        await q.message.reply_text("💬 حالت چت فعال شد")

    elif q.data == "study":
        user_mode[uid] = "study"
        await q.message.reply_text("📚 حالت کمک درسی فعال شد")

    elif q.data == "summary":
        user_mode[uid] = "summary"
        await q.message.reply_text("🧠 حالت خلاصه ساز فعال شد")

# ================== MESSAGE ==================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    mode = user_mode.get(uid, "chat")

    if mode == "study":
        text = "این سوال را ساده و آموزشی حل کن:\n" + text

    elif mode == "summary":
        text = "این متن را خلاصه کن:\n" + text

    await update.message.reply_text("⏳ در حال فکر کردن...")

    reply = ai_engine(uid, text)

    await update.message.reply_text(reply)

# ================== MAIN ==================
def main():
    keep_alive()

    app_bot = Application.builder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(buttons))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("ULTRA AI RUNNING")
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
