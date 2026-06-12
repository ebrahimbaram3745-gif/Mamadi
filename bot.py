import os
import json
from threading import Thread

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# تنظیمات
# =========================

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 7363962357  # آیدی عددی خودت

DATA_DIR = "data"
ANSWERS_FILE = f"{DATA_DIR}/answers.json"
STATS_FILE = f"{DATA_DIR}/stats.json"
USERS_FILE = f"{DATA_DIR}/users.json"

# =========================
# Flask
# =========================

app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web).start()

# =========================
# فایل ها
# =========================

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

answers = load_json(ANSWERS_FILE, {})
stats = load_json(STATS_FILE, {"users": 0, "searches": 0})
users = load_json(USERS_FILE, [])

# =========================
# وضعیت کاربران
# =========================

user_mode = {}

# =========================
# منوها
# =========================

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎮 آمیرزا", callback_data="amirza")
        ],
        [
            InlineKeyboardButton("🥜 فندوق", callback_data="fandogh")
        ],
        [
            InlineKeyboardButton("📊 آمار", callback_data="info")
        ]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back")
        ],
        [
            InlineKeyboardButton("🏠 خانه", callback_data="home")
        ]
    ])

# =========================
# کاربران
# =========================

def register_user(user_id):
    global users

    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, users)

        stats["users"] = len(users)
        save_json(STATS_FILE, stats)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    register_user(update.effective_user.id)

    text = (
        "╔══════════════╗\n"
        "🎮 ربات راهنمای مراحل\n"
        "╚══════════════╝\n\n"
        "یکی از گزینه‌ها را انتخاب کنید:"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu()
    )

# =========================
# دکمه ها
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    if query.data == "home":

        user_mode[uid] = None

        await query.message.reply_text(
            "🏠 منوی اصلی",
            reply_markup=main_menu()
        )

    elif query.data == "back":

        user_mode[uid] = None

        await query.message.reply_text(
            "🔙 بازگشت",
            reply_markup=main_menu()
        )

    elif query.data == "amirza":

        user_mode[uid] = "amirza"

        await query.message.reply_text(
            "🎮 شماره مرحله آمیرزا را وارد کنید:",
            reply_markup=back_menu()
        )

    elif query.data == "fandogh":

        user_mode[uid] = "fandogh"

        await query.message.reply_text(
            "🥜 شماره مرحله فندوق را وارد کنید:",
            reply_markup=back_menu()
        )

    elif query.data == "info":

        text = (
            f"📊 آمار ربات\n\n"
            f"👥 کاربران: {stats['users']}\n"
            f"🔎 جستجوها: {stats['searches']}"
        )

        await query.message.reply_text(
            text,
            reply_markup=main_menu()
        )

# =========================
# جستجو
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text.strip()

    mode = user_mode.get(uid)

    if mode is None:

        await update.message.reply_text(
            "ابتدا بازی را انتخاب کن 👇",
            reply_markup=main_menu()
        )

        return

    if not text.isdigit():

        await update.message.reply_text(
            "❌ فقط شماره مرحله را ارسال کن"
        )

        return

    stage = text

    game_data = answers.get(mode, {})

    result = game_data.get(stage)

    stats["searches"] += 1
    save_json(STATS_FILE, stats)

    if result:

        if isinstance(result, list):
            result_text = "\n".join([f"• {x}" for x in result])
        else:
            result_text = str(result)

        game_name = "آمیرزا" if mode == "amirza" else "فندوق"

        await update.message.reply_text(
            f"🎮 {game_name}\n\n"
            f"📌 مرحله: {stage}\n\n"
            f"{result_text}",
            reply_markup=back_menu()
        )

    else:

        await update.message.reply_text(
            "❌ مرحله پیدا نشد",
            reply_markup=back_menu()
        )

# =========================
# پنل ادمین
# =========================

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        f"📊 آمار ربات\n\n"
        f"👥 کاربران: {stats['users']}\n"
        f"🔎 جستجوها: {stats['searches']}"
    )

# =========================
# MAIN
# =========================

def main():

    keep_alive()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_cmd))

    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("BOT RUNNING")

    app.run_polling()

if __name__ == "__main__":
    main()
