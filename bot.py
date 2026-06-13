import os
import json
import time
import requests
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("7363962357", "0"))

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "VIP Downloader Bot Running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run).start()

# ================= DATA =================
def load(name, default):
    try:
        with open(f"data/{name}.json", "r") as f:
            return json.load(f)
    except:
        return default

def save(name, data):
    with open(f"data/{name}.json", "w") as f:
        json.dump(data, f, indent=2)

users = load("users", {})
vip = load("vip", {})
stats = load("stats", {"downloads": 0})

# ================= LIMIT =================
DAILY_LIMIT = 3

def can_use(uid):
    u = users.get(str(uid), {"count": 0, "time": time.time()})

    # reset daily
    if time.time() - u["time"] > 86400:
        u = {"count": 0, "time": time.time()}

    users[str(uid)] = u
    save("users", users)

    if str(uid) in vip:
        return True

    return u["count"] < DAILY_LIMIT

def use(uid):
    u = users[str(uid)]
    u["count"] += 1
    users[str(uid)] = u
    save("users", users)

# ================= UI =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 دانلود", callback_data="dl")],
        [InlineKeyboardButton("💎 خرید VIP", callback_data="vip")]
    ])

# ================= DOWNLOAD (SIMPLE STABLE) =================
def download(url):
    try:
        r = requests.get(url, timeout=20)
        return r.content
    except:
        return None

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    await update.message.reply_text(
        "🚀 VIP Downloader Bot\n\nلینک بفرست 👇",
        reply_markup=menu()
    )

# ================= BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if q.data == "vip":
        await q.message.reply_text(
            "💎 VIP:\n\n"
            "✔ دانلود نامحدود\n"
            "✔ سرعت بالا\n\n"
            f"📌 برای فعال‌سازی پیام بده به ادمین: {ADMIN_ID}"
        )

    elif q.data == "dl":
        await q.message.reply_text("📥 لینک ارسال کن 👇")

# ================= HANDLE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    url = update.message.text.strip()

    # check limit
    if not can_use(uid):
        await update.message.reply_text("⛔ محدودیت روزانه تمام شد\n💎 برای VIP شدن /start")
        return

    await update.message.reply_text("⏳ در حال دانلود...")

    data = download(url)

    if not data:
        await update.message.reply_text("❌ خطا در دانلود")
        return

    use(uid)
    stats["downloads"] += 1
    save("stats", stats)

    await update.message.reply_document(document=data)

# ================= ADMIN =================
async def addvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = context.args[0]
        vip[uid] = True
        save("vip", vip)
        await update.message.reply_text("✅ VIP اضافه شد")
    except:
        await update.message.reply_text("❌ /addvip user_id")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        f"📊 آمار:\n\n"
        f"📥 دانلودها: {stats['downloads']}\n"
        f"👤 کاربران: {len(users)}\n"
        f"💎 VIP: {len(vip)}"
    )

# ================= MAIN =================
def main():
    if not TOKEN:
        raise Exception("BOT_TOKEN missing")

    keep_alive()

    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("addvip", addvip))
    bot.add_handler(CommandHandler("stats", stats_cmd))
    bot.add_handler(CallbackQueryHandler(buttons))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("💎 VIP BOT RUNNING")
    bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
