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

TOKEN = os.getenv("BOT_TOKEN")

# ================= KEEP ALIVE =================
app = Flask(__name__)

@app.route("/")
def home():
    return "PRO Downloader API Bot Running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run).start()

# ================= UI =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 دانلود لینک", callback_data="dl")],
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")]
    ])

# ================= DETECT =================
def detect(url):
    if "youtu" in url:
        return "youtube"
    if "instagram.com" in url:
        return "instagram"
    if re.search(r"\.(jpg|png|jpeg|webp)$", url):
        return "image"
    if re.search(r"\.(mp4|mov|mkv)$", url):
        return "video"
    return "file"

# ================= YOUTUBE (Piped API) =================
def youtube_download(url):
    try:
        api = f"https://pipedapi.kavin.rocks/streams/{extract_youtube_id(url)}"
        r = requests.get(api, timeout=20)
        data = r.json()

        video_url = data["videoStreams"][0]["url"]
        return requests.get(video_url, timeout=20).content
    except Exception as e:
        return str(e)

def extract_youtube_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else ""

# ================= INSTAGRAM =================
def instagram_download(url):
    try:
        api = "https://snapinsta.io/api/parse"
        r = requests.post(api, data={"url": url}, timeout=20)
        data = r.json()

        media_url = data["media"][0]["url"]
        return requests.get(media_url, timeout=20).content
    except Exception as e:
        return str(e)

# ================= DIRECT =================
def download_direct(url):
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
            "📌 لینک بفرست:\n"
            "- YouTube\n- Instagram\n- عکس\n- ویدیو\n- فایل"
        )

    elif q.data == "dl":
        await q.message.reply_text("📥 لینک را ارسال کن 👇")

# ================= HANDLE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    await update.message.reply_text("⏳ در حال پردازش...")

    t = detect(url)

    # YouTube
    if t == "youtube":
        data = youtube_download(url)
        if isinstance(data, bytes):
            await update.message.reply_video(video=data)
        else:
            await update.message.reply_text("❌ خطا یوتیوب")

    # Instagram
    elif t == "instagram":
        data = instagram_download(url)
        if isinstance(data, bytes):
            await update.message.reply_video(video=data)
        else:
            await update.message.reply_text("❌ خطا اینستا")

    # Image
    elif t == "image":
        data = download_direct(url)
        await update.message.reply_photo(photo=data)

    # Video
    elif t == "video":
        data = download_direct(url)
        await update.message.reply_video(video=data)

    # File
    else:
        data = download_direct(url)
        await update.message.reply_document(document=data)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Downloader PRO API Bot\nلینک بفرست 👇",
        reply_markup=menu()
    )

# ================= MAIN =================
def main():
    if not TOKEN:
        raise Exception("BOT_TOKEN not set")

    keep_alive()

    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(buttons))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 PRO API Downloader Running")
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
