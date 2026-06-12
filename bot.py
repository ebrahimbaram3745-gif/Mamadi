import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "توکن_جدید_ربات"

waiting_users = set()

try:
    with open("answers.json", "r", encoding="utf-8") as f:
        answers = json.load(f)
except:
    answers = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 جستجوی جواب", callback_data="search")]
    ]

    await update.message.reply_text(
        "به ربات جواب مراحل آمیرزا خوش آمدید",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "search":
        waiting_users.add(query.from_user.id)

        await query.message.reply_text(
            "مرحله مورد نظر را وارد کنید:"
        )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in waiting_users:
        return

    stage = update.message.text.strip()

    answer = answers.get(stage)

    if answer:
        await update.message.reply_text(
            f"✅ جواب مرحله {stage}\n\n{answer}"
        )
    else:
        await update.message.reply_text(
            "❌ جواب این مرحله پیدا نشد."
        )

    waiting_users.discard(user_id)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot Started")

    app.run_polling()

if __name__ == "__main__":
    main()
