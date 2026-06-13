import os
import re
import requests
import logging
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= LOG =================
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================= KEEP ALIVE =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Downloader Bot is Running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run).start()

# ================= UI =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 دانلود", callback_data="download")],
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📥 ربات دانلودر هوشمند\n\nلینک بفرست 👇",
        reply_markup=menu()
    )

# ================= DETECT TYPE =================
def detect_link(url: str):
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif re.search(r"\.(mp4|mov|avi|mkv)$", url):
        return "video"
    elif re.search(r"\.(jpg|png|jpeg|webp)$", url):
        return "image"
    else:
        return "file"

# ================= DOWNLOAD (DIRECT FILES) =================
def download_file(url):
    try:
        r = requests.get(url, stream=True, timeout=20)
        return r.content
    except:
        return None

# ================= HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    file_type = detect_link(text)

    if file_type == "youtube":
        await update.message.reply_text("🎥 لینک یوتیوب شناسایی شد\n❌ در نسخه پایه فقط آماده‌سازی داریم")

    elif file_type == "image":
        await update.message.reply_text("🖼 در حال دانلود تصویر...")

        data = download_file(text)
        if data:
            await update.message.reply_photo(photo=data)
        else:
            await update.message.reply_text("❌ دانلود ناموفق بود")

    elif file_type == "video":
        await update.message.reply_text("🎬 ویدیو شناسایی شد\nدر حال ارسال...")

        data = download_file(text)
        if data:
            await update.message.reply_video(video=data)
        else:
            await update.message.reply_text("❌ خطا در دانلود")

    else:
        await update.message.reply_text("📄 فایل معمولی شناسایی شد\nدر حال دانلود...")

        data = download_file(text)
        if data:
            await update.message.reply_document(document=data)
        else:
            await update.message.reply_text("❌ خطا در دانلود")

# ================= CALLBACK =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "help":
        await q.message.reply_text(
            "📌 فقط لینک بفرست\n"
            "- عکس\n- ویدیو\n- فایل مستقیم\n\n"
            "ربات خودش تشخیص میده"
        )

    elif q.data == "download":
        await q.message.reply_text("📥 لینک مورد نظر را ارسال کن")

# ================= MAIN =================
def main():
    if not BOT_TOKEN:
        raise Exception("BOT_TOKEN not set")

    keep_alive()

    app_bot = Application.builder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(buttons))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 Downloader Bot Running")
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
