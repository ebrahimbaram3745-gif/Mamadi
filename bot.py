import os
import json
import logging

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
# LOG
# =========================
logging.basicConfig(level=logging.INFO)

# =========================
# TOKEN
# =========================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("❌ BOT_TOKEN is not set in Render Environment Variables")

# =========================
# STATE
# =========================
user_state = {}

# =========================
# MENU
# =========================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 ابزارها", callback_data="tools")],
        [InlineKeyboardButton("🌍 اطلاعات IP", callback_data="ip")],
        [InlineKeyboardButton("⏰ زمان", callback_data="time")],
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت به منو", callback_data="home")]
    ])

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = None

    await update.message.reply_text(
        "🤖 ربات All Tools (Render Ready)\n\nیکی از گزینه‌ها:",
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
        await q.message.edit_text("🏠 منو اصلی", reply_markup=main_menu())

    elif q.data == "tools":
        user_state[uid] = "tools"
        await q.message.edit_text("🧠 ابزارها فعال شد\nمتن بفرست:", reply_markup=back_menu())

    elif q.data == "ip":
        user_state[uid] = "ip"
        await q.message.edit_text("🌐 IP را ارسال کن:", reply_markup=back_menu())

    elif q.data == "time":
        from datetime import datetime
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await q.message.edit_text(
            f"⏰ UTC Time:\n{now}",
            reply_markup=main_menu()
        )

# =========================
# SIMPLE TOOLS
# =========================
def get_ip_info(ip):
    try:
        import requests
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

    if state == "ip":
        data = get_ip_info(text)
        await update.message.reply_text(json.dumps(data, indent=2))
        return

    if state == "tools":
        await update.message.reply_text(
            f"📦 دریافت شد:\n\n{text}\n\n(ابزار بعدی اینجاست توسعه بدی)",
            reply_markup=main_menu()
        )
        return

    await update.message.reply_text(
        "❗ از منو استفاده کن",
        reply_markup=main_menu()
    )

# =========================
# MAIN (IMPORTANT FOR RENDER)
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    # 🔥 جلوگیری از conflict
    app.bot.delete_webhook(drop_pending_updates=True)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 BOT RUNNING ON RENDER")

    # 🔥 polling پایدار
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()
