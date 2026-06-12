import os
import json
import requests
import logging
from threading import Thread
from bs4 import BeautifulSoup

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ===================== LOG =====================
logging.basicConfig(level=logging.INFO)

# ===================== TOKEN =====================
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise Exception("❌ BOT_TOKEN is missing")

# ===================== FLASK KEEP ALIVE =====================
app_flask = Flask('')

@app_flask.route('/', methods=['GET', 'HEAD'])
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ===================== CACHE =====================
cache = {}

# ===================== DB =====================
try:
    with open("answers.json", "r", encoding="utf-8") as f:
        DB = json.load(f)
except:
    DB = {}

# ===================== USER STATE (مهم) =====================
user_state = {}

# ===================== MENU =====================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 آمیرزا", callback_data="amirza")],
        [InlineKeyboardButton("🥜 فندوق", callback_data="fandogh")]
    ])

# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = None

    await update.message.reply_text(
        "🤖 ربات جواب مراحل\n\nیکی رو انتخاب کن:",
        reply_markup=menu()
    )

# ===================== CALLBACK =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if q.data == "amirza":
        user_state[uid] = "amirza"
        await q.message.reply_text("🔢 شماره مرحله آمیرزا رو وارد کن:")

    elif q.data == "fandogh":
        user_state[uid] = "fandogh"
        await q.message.reply_text("🔢 شماره مرحله فندوق رو وارد کن:")

# ===================== AMIRZA =====================
def scrape_amirza(stage: str):
    try:
        url = "https://www.digikala.com/mag/complete-amirza-guide/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator=" ")

        if stage in text:
            i = text.find(stage)
            return text[i:i+300]

    except:
        pass

    return None

# ===================== FANDOGH =====================
def scrape_fandogh(stage: str):
    try:
        url = "https://par30games.net/266629/fandogh-game-answer/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator=" ")

        if stage in text:
            i = text.find(stage)
            return text[i:i+400]

    except:
        pass

    return None

# ===================== ENGINE =====================
def get_answer(mode: str, stage: str):

    key = f"{mode}:{stage}"

    if key in cache:
        return cache[key]

    if mode == "amirza":
        if stage in DB:
            cache[key] = DB[stage]
            return DB[stage]

        ans = scrape_amirza(stage)

    elif mode == "fandogh":
        ans = scrape_fandogh(stage)

    else:
        return None

    if ans:
        cache[key] = ans

    return ans

# ===================== MESSAGE HANDLER =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    mode = user_state.get(uid)

    if not mode:
        await update.message.reply_text("اول یکی از گزینه‌ها رو انتخاب کن 👇")
        return

    if not text.isdigit():
        await update.message.reply_text("❌ فقط شماره مرحله وارد کن")
        return

    await update.message.reply_text("🔎 در حال جستجو...")

    ans = get_answer(mode, text)

    if ans:
        await update.message.reply_text(f"✅ مرحله {text}\n\n{ans}")
    else:
        await update.message.reply_text("❌ پیدا نشد")

# ===================== MAIN =====================
def main():
    keep_alive()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
