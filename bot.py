import os
import re
import asyncio
import logging
import requests
from flask import Flask
from threading import Thread
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

import yt_dlp

# ================= LOG =================
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

# ================= KEEP ALIVE =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Downloader PRO Bot Running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run).start()

# ================= UI =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 دانلود لینک", callback_data="dl")],
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")],
        [InlineKeyboardButton("⚡ وضعیت", callback_data="status")]
    ])

def back_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Downloader PRO Bot\n\nلینک بفرست یا یکی از گزینه‌ها رو انتخاب کن 👇",
        reply_markup=main_menu()
    )

# ================= DETECT =================
def detect(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if re.search(r"\.(jpg|png|jpeg|webp)$", url):
        return "image"
    if re.search(r"\.(mp4|mov|mkv)$", url):
        return "video"
    return "file"

# ================= YOUTUBE DOWNLOAD =================
def download_youtube(url):
    try:
        ydl_opts = {
            "format": "mp4/best",
            "outtmpl": "video.mp4",
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open("video.mp4", "rb") as f:
            return f.read()

    except Exception as e:
        return str(e)

# ================= DIRECT DOWNLOAD =================
def download_file(url):
    try:
        r = requests.get(url, timeout=20)
        return r.content
    except:
        return None

# ================= CALLBACK =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "help":
        await q.message.reply_text(
            "📌 فقط لینک بفرست\n"
            "- یوتیوب\n- عکس\n- ویدیو\n- فایل\n\n"
            "ربات خودش تشخیص میده",
            reply_markup=back_btn()
        )

    elif q.data == "dl":
        await q.message.reply_text("📥 لینک رو بفرست 👇")

    elif q.data == "status":
        await q.message.reply_text("⚡ ربات آنلاین و آماده دانلود")

    elif q.data == "back":
        await q.message.reply_text("🏠 منوی اصلی", reply_markup=main_menu())

# ================= HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    await update.message.reply_text("⏳ در حال پردازش لینک...")

    t = detect(url)

    if t == "youtube":
        await update.message.reply_text("🎥 دانلود یوتیوب در حال انجام...")

        data = download_youtube(url)

        if isinstance(data, bytes):
            await update.message.reply_video(video=data)
        else:
            await update.message.reply_text(f"❌ خطا: {data}")

    else:
        data = download_file(url)

        if not data:
            await update.message.reply_text("❌ دانلود ناموفق بود")
            return

        if t == "image":
            await update.message.reply_photo(photo=data)

        elif t == "video":
            await update.message.reply_video(video=data)

        else:
            await update.message.reply_document(document=data)

# ================= MAIN =================
def main():
    if not TOKEN:
        raise Exception("BOT_TOKEN not set")

    keep_alive()

    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(buttons))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 PRO Downloader Bot Running")
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
