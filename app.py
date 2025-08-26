import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DELETE_DELAY = int(os.getenv("DELETE_DELAY", "30"))  # زمان پاک‌سازی خودکار (ثانیه)

# شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"سلام! 👋 من بات پاکسازی هستم.\n"
        f"هر پیامی بعد از {DELETE_DELAY} ثانیه پاک میشه 🧹\n"
        f"دستور /clean برای پاک کردن سریع پیام‌هاست."
    )

# پاک‌سازی خودکار بعد از دریافت پیام
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        message = update.message
        chat_id = message.chat_id
        message_id = message.message_id

        # برنامه‌ریزی پاک کردن بعد از DELETE_DELAY ثانیه
        await context.job_queue.run_once(
            delete_message, DELETE_DELAY, data={"chat_id": chat_id, "message_id": message_id}
        )

# تابع واقعی حذف پیام
async def delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    data = job.data
    chat_id = data["chat_id"]
    message_id = data["message_id"]

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"پیام {message_id} در چت {chat_id} پاک شد ✅")
    except Exception as e:
        logger.warning(f"خطا در پاک کردن پیام {message_id}: {e}")

# دستور /clean
async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    # چک کنیم کاربر ادمین باشه
    member = await chat.get_member(user.id)
    if not (member.status in ["administrator", "creator"]):
        await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن از /clean استفاده کنن.")
        return

    try:
        n = int(context.args[0]) if context.args else 5  # تعداد پیام‌ها
    except ValueError:
        n = 5

    # گرفتن تاریخچه آخرین n پیام
    messages = await context.bot.get_chat_history(chat.id, limit=n+1)  # +1 چون پیام /clean خودش هم هست
    deleted = 0
    for msg in messages:
        try:
            await context.bot.delete_message(chat.id, msg.message_id)
            deleted += 1
        except Exception as e:
            logger.warning(f"خطا در حذف پیام {msg.message_id}: {e}")

    await update.message.reply_text(f"✅ {deleted} پیام آخر پاک شد.")

# اجرای اصلی
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
    app.add_handler(CommandHandler("clean", clean))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, auto_delete))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=secret_path,
        webhook_url=f"{public_url}/{secret_path}",
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
