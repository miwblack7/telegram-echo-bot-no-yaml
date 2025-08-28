from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "توکن_ربات_تو_اینجا"  # توکن ربات

app = Flask(__name__)
bot = Bot(token=TOKEN)

# === ساخت اپلیکیشن تلگرام ===
application = ApplicationBuilder().token(TOKEN).build()

# === دستور /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات با موفقیت فعال شد.")

application.add_handler(CommandHandler("start", start))

# === مسیر webhook ===
@app.route("/webhook/<token>", methods=["POST"])
async def webhook(token):
    if token != TOKEN:
        return "Unauthorized", 403
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "ok"

# === مسیر اصلی برای Health Check ===
@app.route("/")
def index():
    return "ربات آماده است!"

# === اجرا محلی (اختیاری) ===
if __name__ == "__main__":
    import asyncio
    asyncio.run(app.run(host="0.0.0.0", port=5000))
