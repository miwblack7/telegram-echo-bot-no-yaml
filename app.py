
import os
import logging
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

async def start(update, context):
    await update.message.reply_text("سلام! من آماده‌ام ✅")

application.add_handler(CommandHandler("start", start))

@flask_app.post(f"/webhook/{WEBHOOK_SECRET}")
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        application.update_queue.put_nowait(update)
    except Exception as e:
        logging.exception("❌ Webhook error:")
        return "error", 500
    return "ok"

@flask_app.get("/ping")
def ping():
    return "ok"

if __name__ == "__main__":
    import asyncio
    asyncio.run(application.initialize())
    bot.set_webhook(f"{APP_URL}/webhook/{WEBHOOK_SECRET}")
    logging.info(f"Bot started with webhook: {APP_URL}/webhook/{WEBHOOK_SECRET}")
    asyncio.run(application.start())
