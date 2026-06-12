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
    raise Exception("❌ BOT_TOKEN is missing in Render Environment Variables")

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

# ===================== LOCAL DB =====================
try:
    with open("answers.json", "r", encoding="utf-8") as f:
        DB = json.load(f)
except:
    DB = {}

# ===================== MENU =====================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 جستجوی جواب آمیرزا", callback_data="search")],
        [InlineKeyboardButton("⚡ پرو حالت", callback_data="pro")],
        [InlineKeyboardButton("🥜 جواب فندوق", callback_data="fandogh")]
    ])

# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 ربات حرفه‌ای جواب مراحل\n\nیکی رو انتخاب کن:",
        reply_markup=menu()
    )

# ===================== CALLBACK =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "search":
        await q.message.reply_text("🔢 شماره مرحله آمیرزا رو وارد کن:")

    elif q.data == "pro":
        await q.message.reply_text("⚡ حالت PRO فعال شد\nفقط شماره مرحله رو بفرست")

    elif q.data == "fandogh":
        await q.message.reply_text("🔎 در حال جستجوی جواب فندوق...")
        await q.message.reply_text(get_fandogh_answer())

# ===================== AMIRZA SCRAPER =====================
def scrape_amirza(stage: str):
    try:
        url = "https://www.digikala.com/mag/complete-amirza-guide/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator=" ")

        if stage in text:
            i = text.find(stage)
            return text[i:i+300]

    except Exception as e:
        print("amirza scrape error:", e)

    return None

# ===================== FANDOGH SCRAPER =====================
def get_fandogh_answer():
    try:
        url = "https://par30games.net/266629/fandogh-game-answer/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(separator=" ")

        return text[:1200]

    except Exception as e:
        return f"❌ خطا در فندوق: {e}"

# ===================== ENGINE =====================
def get_answer(stage: str):

    if stage in cache:
        return cache[stage]

    if stage in DB:
        cache[stage] = DB[stage]
        return DB[stage]

    site = scrape_amirza(stage)
    if site:
        cache[stage] = site
        return site

    return None

# ===================== MESSAGE HANDLER =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("❌ فقط شماره مرحله وارد کن")
        return

    await update.message.reply_text("🔎 در حال جستجو...")

    ans = get_answer(text)

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
