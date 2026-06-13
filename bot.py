import os
import json
import requests
from datetime import datetime
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
        [InlineKeyboardButton("🔤 مترجم", callback_data="translate")],
        [InlineKeyboardButton("📱 QR ساز", callback_data="qr")],
        [InlineKeyboardButton("🌐 IP Info", callback_data="ipinfo")],
        [InlineKeyboardButton("⏰ زمان جهانی", callback_data="time")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت به منو", callback_data="home")]
    ])

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = None

    await update.message.reply_text(
        "🤖 All Tools Bot\nیکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=main_menu()
    )

# =========================
# CALLBACK
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    # HOME
    if q.data == "home":
        user_state[uid] = None
        await q.message.edit_text("🏠 منو اصلی", reply_markup=main_menu())

    # TOOLS MENU
    elif q.data == "tools":
        user_state[uid] = None
        await q.message.edit_text("🧠 ابزارها:", reply_markup=tools_menu())

    # BACK
    elif q.data == "back":
        user_state[uid] = None
        await q.message.edit_text("🏠 برگشت", reply_markup=main_menu())

    # TRANSLATE
    elif q.data == "translate":
        user_state[uid] = "translate"
        await q.message.edit_text(
            "🔤 متن رو بفرست تا ترجمه کنم (فعلاً EN → FA)",
            reply_markup=back_menu()
        )

    # QR
    elif q.data == "qr":
        user_state[uid] = "qr"
        await q.message.edit_text(
            "📱 متن رو بفرست تا QR بسازم",
            reply_markup=back_menu()
        )

    # IP INFO
    elif q.data == "ipinfo":
        user_state[uid] = "ip"
        await q.message.edit_text(
            "🌐 IP رو بفرست:",
            reply_markup=back_menu()
        )

    # TIME
    elif q.data == "time":
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await q.message.edit_text(
            f"⏰ زمان UTC:\n{now}",
            reply_markup=tools_menu()
        )

# =========================
# TRANSLATE API (بدون دردسر)
# =========================

def translate(text):
    url = "https://api.mymemory.translated.net/get"
    r = requests.get(url, params={
        "q": text,
        "langpair": "en|fa"
    })
    return r.json()["responseData"]["translatedText"]

# =========================
# QR API
# =========================

def make_qr(text):
    return f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={text}"

# =========================
# IP INFO
# =========================

def ip_info(ip):
    r = requests.get(f"https://ipinfo.io/{ip}/json")
    return r.json()

# =========================
# MESSAGE HANDLER
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    state = user_state.get(uid)

    # TRANSLATE
    if state == "translate":
        result = translate(text)
        await update.message.reply_text(f"🌍 ترجمه:\n{result}")
        return

    # QR
    if state == "qr":
        url = make_qr(text)
        await update.message.reply_photo(photo=url, caption="📱 QR Code")
        return

    # IP
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
