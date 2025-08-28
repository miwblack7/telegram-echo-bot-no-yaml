import os
import logging
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret")
APP_URL = os.getenv("APP_URL")

if not TELEGRAM_TOKEN or not APP_URL:
    raise RuntimeError("Env vars TELEGRAM_TOKEN و APP_URL باید تنظیم شوند.")

logging.basicConfig(level=logging.INFO)

flask_app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# دستور start
async def start(update, context):
    await update.message.reply_text("سلام! من آماده‌ام ✅")

application.add_handler(CommandHandler("start", start))

# وبهوک
@flask_app.post(f"/webhook/{WEBHOOK_SECRET}")
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    asyncio.get_event_loop().create_task(application.update_queue.put(update))
    return "ok"

# مسیر Health Check
@flask_app.get("/")
def health():
    return "ok", 200

# اجرای سرور و loop برای پردازش handler ها
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.initialize())
    bot.set_webhook(f"{APP_URL}/webhook/{WEBHOOK_SECRET}")
    logging.info(f"Bot started with webhook: {APP_URL}/webhook/{WEBHOOK_SECRET}")

    # ایجاد task برای پردازش update_queue
    loop.create_task(application.start())
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
