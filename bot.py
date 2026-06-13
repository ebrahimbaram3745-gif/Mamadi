import os
import requests
import logging
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================== CONFIG ==================
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================== KEEP ALIVE ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "AI Bot Running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run).start()

# ================== STATE ==================
user_mode = {}
user_translate_lang = {}

# ================== MENU ==================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 چت AI", callback_data="chat")],
        [InlineKeyboardButton("🌐 ترجمه متن", callback_data="translate")],
        [InlineKeyboardButton("📚 کمک درسی", callback_data="study")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت", callback_data="back")]
    ])

def lang_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇹🇷 Turkish", callback_data="lang_tr")
        ],
        [
            InlineKeyboardButton("🇸🇦 Arabic", callback_data="lang_ar"),
            InlineKeyboardButton("🇩🇪 German", callback_data="lang_de")
        ],
        [
            InlineKeyboardButton("🇫🇷 French", callback_data="lang_fr")
        ],
        [
            InlineKeyboardButton("🔙 برگشت", callback_data="back")
        ]
    ])

# ================== TRANSLATE ==================
def translate_text(text, target_lang):
    try:
        url = "https://translate.googleapis.com/translate_a/single"

        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        return data[0][0][0]

    except:
        return "❌ خطا در ترجمه"

# ================== AI SIMPLE ==================
def ai_reply(text):
    try:
        return f"🧠 پاسخ AI:\n\n{text}\n\n(نسخه ساده فعال است)"
    except:
        return "❌ خطا"

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Ultra AI Bot\nیک گزینه انتخاب کن:",
        reply_markup=main_menu()
    )

# ================== CALLBACK ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    # برگشت
    if q.data == "back":
        user_mode[uid] = None
        await q.message.reply_text("🏠 منو اصلی", reply_markup=main_menu())

    # چت
    elif q.data == "chat":
        user_mode[uid] = "chat"
        await q.message.reply_text("💬 حالت چت فعال شد", reply_markup=back_menu())

    # کمک درسی
    elif q.data == "study":
        user_mode[uid] = "study"
        await q.message.reply_text("📚 حالت درس فعال شد", reply_markup=back_menu())

    # ترجمه
    elif q.data == "translate":
        user_mode[uid] = "translate"
        await q.message.reply_text("🌐 زبان را انتخاب کن:", reply_markup=lang_menu())

    # انتخاب زبان
    elif q.data.startswith("lang_"):
        lang = q.data.split("_")[1]
        user_translate_lang[uid] = lang
        await q.message.reply_text(f"✏️ متن را برای ترجمه به {lang} ارسال کن", reply_markup=back_menu())

# ================== MESSAGE ==================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    mode = user_mode.get(uid)

    if mode == "translate":
        lang = user_translate_lang.get(uid, "en")
        result = translate_text(text, lang)

        await update.message.reply_text(
            f"🌐 ترجمه:\n\n{result}",
            reply_markup=back_menu()
        )
        return

    if mode == "study":
        text = "این سوال را آموزشی حل کن:\n" + text

    await update.message.reply_text(ai_reply(text))

# ================== MAIN ==================
def main():
    keep_alive()

    app_bot = Application.builder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(buttons))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("BOT RUNNING")
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
