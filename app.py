import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("سلام! 👋 من یک بات ساده هستم.\nهرچی بفرستی، همونو برمی‌گردونم 🤖")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)

def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("Env var TELEGRAM_TOKEN تنظیم نشده است.")

    secret_path = os.getenv("WEBHOOK_SECRET", "super-secret-path")
    public_url  = os.getenv("PUBLIC_URL")
    if not public_url:
        raise RuntimeError("Env var PUBLIC_URL تنظیم نشده است.")

    port = int(os.getenv("PORT", "8000"))

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=secret_path,
        webhook_url=f"{public_url}/{secret_path}",
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
