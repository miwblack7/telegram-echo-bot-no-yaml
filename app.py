import os
import logging
import asyncio
from asyncio import run_coroutine_threadsafe
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

# ایجاد loop جدید
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ایجاد Application
application = Application.builder().token(TELEGRAM_TOKEN).build()
loop.run_until_complete(application.initialize())

# دستور start
async def start(update, context):
    await update.message.reply_text("سلام! من آماده‌ام ✅")

application.add_handler(CommandHandler("start", start))

# وبهوک
@flask_app.post(f"/webhook/{WEBHOOK_SECRET}")
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    # ارسال update به queue به صورت thread-safe با loop خودمان
    run_coroutine_threadsafe(application.update_queue.put(update), loop)
    return "ok"

# مسیر Health Check
@flask_app.get("/")
def health():
    return "ok", 200

# اجرای سرور و پردازش handler ها
if __name__ == "__main__":
    bot.set_webhook(f"{APP_URL}/webhook/{WEBHOOK_SECRET}")
    logging.info(f"Bot started with webhook: {APP_URL}/webhook/{WEBHOOK_SECRET}")

    # ایجاد task برای پردازش update_queue
    loop.create_task(application.start())
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
