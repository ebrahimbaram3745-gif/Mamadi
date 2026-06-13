import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

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
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN not set")

user_state = {}

# =========================
# MENUS (PRO UI)
# =========================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 ابزارها", callback_data="tools")],
        [InlineKeyboardButton("🌐 ابزار آنلاین PRO", callback_data="online")]
    ])

def tools_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔤 مترجم", callback_data="translate"),
            InlineKeyboardButton("📱 QR", callback_data="qr")
        ],
        [
            InlineKeyboardButton("🌐 IP Pro", callback_data="ipinfo"),
            InlineKeyboardButton("⏰ تاریخ", callback_data="time")
        ],
        [
            InlineKeyboardButton("🏠 منو اصلی", callback_data="home")
        ]
    ])

def online_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔎 جستجوی وب", callback_data="websearch"),
            InlineKeyboardButton("📰 اخبار", callback_data="news")
        ],
        [
            InlineKeyboardButton("🌦 آب و هوا", callback_data="weather"),
            InlineKeyboardButton("💱 ارز", callback_data="currency")
        ],
        [
            InlineKeyboardButton("🤖 AI ساده", callback_data="ai"),
            InlineKeyboardButton("🌐 IP پیشرفته", callback_data="ippro")
        ],
        [
            InlineKeyboardButton("🔙 برگشت", callback_data="home")
        ]
    ])

def back_to_online():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت", callback_data="online")]
    ])

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = None

    await update.message.reply_text(
        "🤖 All Tools Bot PRO\n\nیکی از گزینه‌ها:",
        reply_markup=main_menu()
    )

# =========================
# CALLBACK ROUTER
# =========================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    # HOME
    if q.data == "home":
        user_state[uid] = None
        await q.message.edit_text("🏠 منو اصلی", reply_markup=main_menu())

    # TOOLS
    elif q.data == "tools":
        user_state[uid] = None
        await q.message.edit_text("🧠 ابزارها", reply_markup=tools_menu())

    # ONLINE HUB
    elif q.data == "online":
        user_state[uid] = None
        await q.message.edit_text("🌐 ابزار آنلاین PRO", reply_markup=online_menu())

    # ================= ONLINE TOOLS =================

    elif q.data == "websearch":
        user_state[uid] = "websearch"
        await q.message.edit_text("🔎 متن برای جستجو بفرست:", reply_markup=back_to_online())

    elif q.data == "news":
        await q.message.edit_text(get_news(), reply_markup=back_to_online())

    elif q.data == "weather":
        user_state[uid] = "weather"
        await q.message.edit_text("🌦 نام شهر رو بفرست:", reply_markup=back_to_online())

    elif q.data == "currency":
        user_state[uid] = "currency"
        await q.message.edit_text("💱 مثل: USD IRR", reply_markup=back_to_online())

    elif q.data == "ai":
        user_state[uid] = "ai"
        await q.message.edit_text("🤖 سوالت رو بپرس:", reply_markup=back_to_online())

    elif q.data == "ippro":
        user_state[uid] = "ippro"
        await q.message.edit_text("🌐 IP رو بفرست:", reply_markup=back_to_online())

# =========================
# ONLINE FUNCTIONS
# =========================

def get_news():
    try:
        r = requests.get("https://www.bbc.com/news", timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        return "📰 آخرین خبرها:\n\n" + text[:500]
    except:
        return "❌ خبر دریافت نشد"

def web_search(query):
    try:
        url = "https://duckduckgo.com/html/"
        r = requests.post(url, data={"q": query}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.get_text(" ", strip=True)[:500]
    except:
        return "❌ سرچ انجام نشد"

def weather(city):
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=10)
        return "🌦 " + r.text
    except:
        return "❌ آب و هوا خطا"

def currency(text):
    try:
        base, target = text.split()
        url = f"https://api.exchangerate.host/convert?from={base}&to={target}"
        r = requests.get(url)
        data = r.json()
        return f"💱 {base} → {target}\n{data['result']}"
    except:
        return "❌ فرمت اشتباه"

def ai_simple(text):
    return f"🤖 پاسخ هوشمند:\n\n{text[::-1]}"

def ip_pro(ip):
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json")
        return json.dumps(r.json(), indent=2)
    except:
        return "❌ خطا"

# =========================
# MESSAGE HANDLER
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    state = user_state.get(uid)

    if state == "websearch":
        await update.message.reply_text(web_search(text))
        return

    if state == "weather":
        await update.message.reply_text(weather(text))
        return

    if state == "currency":
        await update.message.reply_text(currency(text))
        return

    if state == "ai":
        await update.message.reply_text(ai_simple(text))
        return

    if state == "ippro":
        await update.message.reply_text(ip_pro(text))
        return

    await update.message.reply_text(
        "❗ از منو استفاده کن",
        reply_markup=main_menu()
    )

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 BOT RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
