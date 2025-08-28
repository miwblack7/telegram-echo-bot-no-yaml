from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler

# === تنظیمات ===
TOKEN = "توکن_ربات_تو_اینجا"  # توکن ربات را از BotFather بگیر

# === ساخت برنامه Flask و Bot ===
app = Flask(__name__)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, None)

# === دستور ساده /start ===
def start(update: Update, context):
    update.message.reply_text("سلام! ربات با موفقیت فعال شد.")

dp.add_handler(CommandHandler("start", start))

# === مسیر webhook ===
@app.route("/webhook/<token>", methods=["POST"])
def webhook(token):
    if token != TOKEN:
        return "Unauthorized", 403
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return "ok"

# === مسیر اصلی برای بررسی ===
@app.route("/")
def index():
    return "ربات آماده است!"

# === اگر بخواهی محلی اجرا کنی ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
