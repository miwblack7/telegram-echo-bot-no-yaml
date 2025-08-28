import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 5000))

if not TOKEN:
    raise ValueError("لطفاً توکن ربات را در TELEGRAM_TOKEN وارد کنید!")

# Flask app
app = Flask(__name__)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من ربات شما هستم!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"شما نوشتید: {text}")

# Telegram bot application
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("echo", echo))

# Flask route for Telegram webhook
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.update_queue.put(update))
    return "OK"

# Optional: health check
@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

# Start Flask app (for local testing)
if __name__ == "__main__":
    application.run_polling()  # فقط برای تست محلی، روی Render از webhook استفاده می‌کنیم
