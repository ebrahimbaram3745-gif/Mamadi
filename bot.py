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

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)

# ---------------- TOKEN (FIXED) ----------------
TOKEN = os.environ.get("8843057441:AAG3vIg4g6oGb1NerGH6arzblOwAGQShxD4")

if not TOKEN:
    raise Exception("❌ BOT_TOKEN is not set in Render Environment Variables")

# ---------------- MEMORY ----------------
waiting_users = set()

# ---------------- LOAD ANSWERS ----------------
try:
    with open("answers.json", "r", encoding="utf-8") as f:
        answers = json.load(f)
except:
    answers = {}

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 دریافت جواب مرحله", callback_data="search")]
    ]

    await update.message.reply_text(
        "👋 به ربات آمیرزا خوش آمدی\n\nیکی از گزینه‌ها را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- BUTTONS ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "search":
        waiting_users.add(query.from_user.id)

        await query.message.reply_text(
            "🔢 شماره مرحله را وارد کن:"
        )

# ---------------- MESSAGE HANDLER ----------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in waiting_users:
        return

    answer = answers.get(text)

    if answer:
        await update.message.reply_text(
            f"✅ مرحله {text}\n\n{answer}"
        )
    else:
        await update.message.reply_text(
            "❌ برای این مرحله جوابی ثبت نشده"
        )

    waiting_users.discard(user_id)

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
