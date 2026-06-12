import os
import json
import requests
from collections import defaultdict
from threading import Thread
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

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN is missing")

# ================= FLASK KEEP ALIVE =================
app = Flask(__name__)

@app.route("/")
def home():
    return "AI PRO Bot Running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()

# ================= MEMORY SYSTEM =================
memory = defaultdict(list)

stats = {
    "users": set(),
    "messages": 0
}

# ================= UI =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 چت هوش مصنوعی", callback_data="chat")],
        [InlineKeyboardButton("📚 حل سوال درسی", callback_data="study")],
        [InlineKeyboardButton("🔎 جستجوی وب", callback_data="search")],
        [InlineKeyboardButton("📰 اخبار روز", callback_data="news")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    stats["users"].add(uid)

    await update.message.reply_text(
        "🤖 ربات PRO AI فعال شد\nیکی از گزینه‌ها را انتخاب کن:",
        reply_markup=menu()
    )

# ================= CALLBACK =================
user_mode = {}

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if q.data == "chat":
        user_mode[uid] = "chat"
        await q.message.reply_text("💬 سوالت رو بپرس")

    elif q.data == "study":
        user_mode[uid] = "study"
        await q.message.reply_text("📚 سوال درسی را ارسال کن (با توضیح کامل جواب می‌دم)")

    elif q.data == "search":
        user_mode[uid] = "search"
        await q.message.reply_text("🔎 عبارت جستجو را بفرست")

    elif q.data == "news":
        news = get_news()
        await q.message.reply_text(news)

# ================= AI ENGINE =================
def ai_response(user_id, text, mode):

    # حافظه گفتگو
    memory[user_id].append(text)
    history = "\n".join(memory[user_id][-5:])

    if mode == "chat":
        return f"🤖 پاسخ هوشمند:\n\n{text}\n\n🧠 حافظه:\n{history}"

    elif mode == "study":
        return f"📚 حل آموزشی:\n\nموضوع: {text}\n\n💡 توضیح:\nاین سوال را مرحله به مرحله تحلیل می‌کنم...\n(نسخه پرو قابل اتصال به GPT دارد)"

    elif mode == "search":
        return web_search(text)

    return "از منو استفاده کن"

# ================= WEB SEARCH =================
def web_search(query):
    try:
        url = f"https://duckduckgo.com/?q={query}"
        return f"🔎 نتیجه جستجو:\n{url}"
    except:
        return "❌ خطا در جستجو"

# ================= NEWS =================
def get_news():
    try:
        r = requests.get("https://www.aljazeera.com/xml/rss/all.xml", timeout=10)
        if r.status_code == 200:
            return "📰 آخرین اخبار دریافت شد (نسخه ساده)\n\nبرای نسخه حرفه‌ای RSS کامل اضافه می‌شود"
        return "❌ خبر پیدا نشد"
    except:
        return "❌ خطا در دریافت خبر"

# ================= MESSAGE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text

    stats["users"].add(uid)
    stats["messages"] += 1

    mode = user_mode.get(uid)

    if not mode:
        await update.message.reply_text("از منو انتخاب کن 👇", reply_markup=menu())
        return

    reply = ai_response(uid, text, mode)

    await update.message.reply_text(reply)

# ================= MAIN =================
def main():
    keep_alive()

    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(buttons))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 PRO AI BOT RUNNING")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
