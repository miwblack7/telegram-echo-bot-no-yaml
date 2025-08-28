# app.py
import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# متغیرهای محیطی
TOKEN = os.environ.get("TELEGRAM_TOKEN")  # توکن ربات
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # URL وبهوک

# ساخت اپلیکیشن Flask
app = Flask(__name__)

# ساخت اپلیکیشن تلگرام
application = ApplicationBuilder().token(TOKEN).build()

# -------------------------
# دستورات ربات
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من ربات شما هستم.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستورات موجود:\n/start\n/help\n/echo")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # همان متن کاربر را جواب می‌دهد
    text = update.message.text
    await update.message.reply_text(f"پیام شما: {text}")

# اضافه کردن دستورات به اپلیکیشن تلگرام
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("echo", echo))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# -------------------------
# مسیر وبهوک
# -------------------------
@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.update_queue.put(update)
    return "OK", 200

# مسیر اصلی برای تست
@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است!", 200

# -------------------------
# تنظیم وبهوک
# -------------------------
async def set_webhook():
    await application.bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook set to {WEBHOOK_URL}")

# -------------------------
# اجرای ربات
# -------------------------
if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
