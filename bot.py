import os
import requests
import logging
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================== CONFIG ==================
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
OPENAI_KEY = os.getenv("OPENAI_KEY")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is missing")

# ================== FLASK KEEP ALIVE ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "AI Bot Running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run).start()

# ================== AI: GEMINI ==================
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

# ================== AI: OPENAI ==================
def ask_openai(text):
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

# ================== FALLBACK ==================
def fallback_answer(text):
    return f"🤖 پاسخ ساده:\n\nمن الان دسترسی AI ندارم، ولی سوال شما:\n{text}\n\n(لطفاً بعداً دوباره امتحان کنید)"

# ================== MAIN AI ENGINE ==================
def smart_ai(text):

    # 1. Gemini
    result = ask_gemini(text)
    if result:
        return "🧠 Gemini:\n\n" + result

    # 2. GPT
    result = ask_openai(text)
    if result:
        return "🤖 GPT:\n\n" + result

    # 3. Fallback
    return fallback_answer(text)

# ================== TELEGRAM ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🤖 AI Chat", callback_data="ai")]
    ]

    await update.message.reply_text(
        "🤖 AI Bot Ready\nپیام بده جواب بگیر",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    await update.message.reply_text("⏳ در حال پردازش...")

    reply = smart_ai(text)

    await update.message.reply_text(reply)

# ================== MAIN ==================
def main():
    keep_alive()

    app_bot = Application.builder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("BOT RUNNING...")
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
