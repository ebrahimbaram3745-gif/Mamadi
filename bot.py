import os
import json
import logging
import requests
from bs4 import BeautifulSoup

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ---------------- CONFIG ----------------
logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN is not set")

# ---------------- CACHE ----------------
cache = {}

# ---------------- LOCAL DB ----------------
try:
    with open("answers.json", "r", encoding="utf-8") as f:
        LOCAL_DB = json.load(f)
except:
    LOCAL_DB = {}

# ---------------- UI ----------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 جستجوی جواب مرحله", callback_data="search")],
        [InlineKeyboardButton("ℹ️ درباره", callback_data="about")]
    ])

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 ربات آمیرزا حرفه‌ای\n\nیکی از گزینه‌ها را انتخاب کن:",
        reply_markup=main_menu()
    )

# ---------------- CALLBACK ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "search":
        await q.message.reply_text("🔢 شماره مرحله را وارد کن:")

    elif q.data == "about":
        await q.message.reply_text("🤖 ساخته شده برای دریافت جواب مراحل آمیرزا")

# ---------------- SCRAPER (SITE MODE) ----------------
def scrape_from_site(stage: str):
    try:
        url = "https://www.digikala.com/mag/complete-amirza-guide/"

        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text()

        # ساده: پیدا کردن شماره مرحله داخل متن
        if stage in text:
            idx = text.find(stage)
            return text[idx:idx+200]

    except Exception as e:
        print("scrape error:", e)

    return None

# ---------------- CORE SEARCH ----------------
def get_answer(stage: str):
    if stage in cache:
        return cache[stage]

    # 1. local DB
    if stage in LOCAL_DB:
        cache[stage] = LOCAL_DB[stage]
        return LOCAL_DB[stage]

    # 2. scraping site
    site_answer = scrape_from_site(stage)
    if site_answer:
        cache[stage] = site_answer
        return site_answer

    return None

# ---------------- MESSAGE ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage = update.message.text.strip()

    if not stage.isdigit():
        await update.message.reply_text("❌ فقط شماره مرحله وارد کن")
        return

    await update.message.reply_text("🔎 در حال جستجو...")

    answer = get_answer(stage)

    if answer:
        await update.message.reply_text(
            f"✅ مرحله {stage}\n\n{answer}"
        )
    else:
        await update.message.reply_text(
            "❌ جواب پیدا نشد"
        )

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
