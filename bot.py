import os
import json
import requests
from datetime import datetime

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

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN not set")

user_state = {}

# =========================
# MENU
# =========================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 ابزارها", callback_data="tools")],
        [InlineKeyboardButton("🌍 ابزار آنلاین", callback_data="online")],
    ])

def tools_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔤 مترجم", callback_data="translate"),
            InlineKeyboardButton("📱 QR ساز", callback_data="qr")
        ],
        [
            InlineKeyboardButton("🌐 IP Info", callback_data="ipinfo"),
            InlineKeyboardButton("⏰ تاریخ امروز", callback_data="time")
        ],
        [
            InlineKeyboardButton("🏠 منو اصلی", callback_data="home")
        ]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت به ابزارها", callback_data="tools")]
    ])

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = None

    await update.message.reply_text(
        "🤖 All Tools Bot Pro\n\nیکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=main_menu()
    )

# =========================
# CALLBACK
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if q.data == "home":
        user_state[uid] = None
        await q.message.edit_text("🏠 منوی اصلی", reply_markup=main_menu())

    elif q.data == "tools":
        user_state[uid] = None
        await q.message.edit_text("🧠 ابزارها:", reply_markup=tools_menu())

    elif q.data == "translate":
        user_state[uid] = "translate"
        await q.message.edit_text(
            "🔤 متن رو بفرست تا ترجمه کنم (EN → FA)",
            reply_markup=back_menu()
        )

    elif q.data == "qr":
        user_state[uid] = "qr"
        await q.message.edit_text(
            "📱 متن رو بفرست تا QR بسازم",
            reply_markup=back_menu()
        )

    elif q.data == "ipinfo":
        user_state[uid] = "ip"
        await q.message.edit_text(
            "🌐 IP رو ارسال کن:",
            reply_markup=back_menu()
        )

    elif q.data == "time":
        now = get_persian_time()

        await q.message.edit_text(
            f"⏰ تاریخ امروز:\n\n{now}",
            reply_markup=tools_menu()
        )

# =========================
# TIME FROM WEBSITE
# =========================

def get_persian_time():
    try:
        url = "https://www.bahesab.ir/time/today/"
        r = requests.get(url, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        return text[:300]

    except Exception as e:
        return f"❌ خطا در دریافت زمان: {e}"

# =========================
# TRANSLATE
# =========================

def translate(text):
    try:
        url = "https://api.mymemory.translated.net/get"
        r = requests.get(url, params={
            "q": text,
            "langpair": "en|fa"
        }, timeout=10)

        return r.json()["responseData"]["translatedText"]
    except:
        return "❌ خطا در ترجمه"

# =========================
# QR
# =========================

def make_qr(text):
    return f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={text}"

# =========================
# IP INFO
# =========================

def ip_info(ip):
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
        return r.json()
    except:
        return {"error": "failed"}

# =========================
# MESSAGE HANDLER
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    state = user_state.get(uid)

    if state == "translate":
        result = translate(text)
        await update.message.reply_text(f"🌍 ترجمه:\n{result}")
        return

    if state == "qr":
        url = make_qr(text)
        await update.message.reply_photo(photo=url, caption="📱 QR Code")
        return

    if state == "ip":
        data = ip_info(text)
        await update.message.reply_text(json.dumps(data, indent=2))
        return

    await update.message.reply_text(
        "❗ از منو استفاده کن",
        reply_markup=main_menu()
    )

# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(TOKEN).build()

    # جلوگیری از conflict
    app.bot.delete_webhook(drop_pending_updates=True)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 BOT RUNNING")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
