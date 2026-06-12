import os
import requests
from threading import Thread
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ================= KEYS =================
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not TOKEN:
    raise Exception("BOT_TOKEN missing")

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "ULTRA AI BOT RUNNING"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()

# ================= MEMORY =================
memory = {}

user_mode = {}

# ================= MENU =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 چت AI (Ultra)", callback_data="chat")],
        [InlineKeyboardButton("📚 حل سوال درسی", callback_data="study")],
        [InlineKeyboardButton("🧠 Gemini Mode", callback_data="gemini")],
        [InlineKeyboardButton("⚡ GPT Mode", callback_data="gpt")],
        [InlineKeyboardButton("🔎 جستجو", callback_data="search")]
    ])

# ================= AI: OPENAI =================
def ask_openai(text):
    if not OPENAI_KEY:
        return "❌ OpenAI API ندارد"

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": text}]
            },
            timeout=20
        )

        return r.json()["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ GPT Error: {e}"

# ================= AI: GEMINI =================
def ask_gemini(text):
    if not GEMINI_KEY:
        return "❌ Gemini API ندارد"

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

        r = requests.post(url, json={
            "contents": [{
                "parts": [{"text": text}]
            }]
        }, timeout=20)

        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"❌ Gemini Error: {e}"

# ================= ROUTER (ULTRA BRAIN) =================
def smart_ai(text):

    gpt = ask_openai(text)
    gemini = ask_gemini(text)

    # انتخاب بهترین جواب (ساده ولی کاربردی)
    if len(gpt) > len(gemini):
        return f"🤖 GPT Answer:\n{gpt}\n\n🧠 Gemini Backup:\n{gemini}"
    else:
        return f"🧠 Gemini Answer:\n{gemini}\n\n🤖 GPT Backup:\n{gpt}"

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 ULTRA AI BOT فعال شد", reply_markup=menu())

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_mode[q.from_user.id] = q.data

    await q.message.reply_text("✍️ پیام خود را ارسال کنید")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text

    mode = user_mode.get(uid, "chat")

    if mode == "gpt":
        reply = ask_openai(text)

    elif mode == "gemini":
        reply = ask_gemini(text)

    elif mode == "study":
        reply = ask_openai("حل آموزشی و مرحله‌ای: " + text)

    else:
        reply = smart_ai(text)

    await update.message.reply_text(reply)

# ================= MAIN =================
def main():
    keep_alive()

    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(buttons))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🔥 ULTRA AI BOT RUNNING")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
