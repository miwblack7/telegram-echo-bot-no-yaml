from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, Dispatcher, CallbackContext

import os

# مقدار توکن ربات که از BotFather گرفتید
TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # مثلا "https://yourapp.onrender.com/webhook"

bot = Bot(token=TOKEN)
app = Flask(__name__)

# Dispatcher برای مدیریت دستورات
dispatcher = Dispatcher(bot, None, workers=0)

# دستور /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! من ربات شما هستم.")

# دستور /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("دستورات موجود:\n/start\n/help")

# اضافه کردن دستورها به دیسپچر
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))

# مسیر وبهوک
@app.route(f"/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# روت اصلی برای چک کردن سرور
@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است!", 200

# تنظیم وبهوک روی تلگرام
def set_webhook():
    bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook set to {WEBHOOK_URL}")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
