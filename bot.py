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
    return "ANTI BUG AI BOT RUNNING"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()

# ================= STATE =================
user_mode = {}

# ================= MENUS =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 چت AI", callback_data="chat")],
        [InlineKeyboardButton("📚 حل درس", callback_data="study")],
        [InlineKeyboardButton("⚡ GPT", callback_data="gpt")],
        [InlineKeyboardButton("🧠 Gemini", callback_data="gemini")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
    ])

# ================= OPENAI =================
def ask_openai(text):
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

        data = r.json()

        if "error" in data:
            return f"❌ GPT Error: {data['error']['message']}"

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ GPT Exception: {e}"

# ================= GEMINI =================
def ask_gemini(text):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

        r = requests.post(url, json={
            "contents": [{"parts": [{"text": text}]}]
        }, timeout=20)

        data = r.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"❌ Gemini Error: {e}"

# ================= SMART AI =================
def smart_ai(text):
    gpt = ask_openai(text)
    gemini = ask_gemini(text)

    if len(str(gpt)) > len(str(gemini)):
        return f"🤖 GPT:\n{gpt}\n\n🧠 Gemini backup:\n{gemini}"
    else:
        return f"🧠 Gemini:\n{gemini}\n\n🤖 GPT backup:\n{gpt}"

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 ربات AI ضد باگ فعال شد",
        reply_markup=main_menu()
    )

# ================= CALLBACK (EDIT MESSAGE - مهم) =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    # فقط حالت رو ذخیره می‌کنیم
    user_mode[uid] = q.data

    text_map = {
        "chat": "💬 حالت چت AI فعال شد\nپیام خود را ارسال کنید:",
        "study": "📚 حالت درسی فعال شد\nسوال خود را بفرست:",
        "gpt": "⚡ حالت GPT فعال شد",
        "gemini": "🧠 حالت Gemini فعال شد"
    }

    msg = text_map.get(q.data, "انتخاب شد")

    # 🔥 مهم: EDIT پیام (نه ارسال پیام جدید)
    await q.message.edit_text(
        msg,
        reply_markup=back_menu()
    )

# ================= BACK =================
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    user_mode.pop(uid, None)

    await q.message.edit_text(
        "🏠 منوی اصلی",
        reply_markup=main_menu()
    )

# ================= HANDLE MESSAGE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    mode = user_mode.get(uid, "chat")

    if mode == "gpt":
        reply = ask_openai(text)

    elif mode == "gemini":
        reply = ask_gemini(text)

    elif mode == "study":
        reply = ask_openai("حل آموزشی مرحله‌ای: " + text)

    else:
        reply = smart_ai(text)

    await update.message.reply_text(reply, reply_markup=back_menu())

# ================= MAIN =================
def main():
    keep_alive()

    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(buttons))
    app_bot.add_handler(CallbackQueryHandler(back, pattern="back"))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🔥 ANTI BUG AI RUNNING")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
