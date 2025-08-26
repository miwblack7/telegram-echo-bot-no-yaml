import os
import logging
from collections import deque
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DELETE_DELAY = int(os.getenv("DELETE_DELAY", "30"))  # زمان پاک‌سازی خودکار (ثانیه)

# ذخیره پیام‌ها (آخرین 1000 پیام)
message_buffer = deque(maxlen=1000)

# شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"سلام! 👋 من بات پاکسازی هستم.\n"
        f"هر پیامی بعد از {DELETE_DELAY} ثانیه پاک میشه 🧹\n"
        f"و می‌تونی با /clean [n] آخرین پیام‌های گپ رو پاک کنی."
    )

# ذخیره پیام و پاک‌سازی خودکار
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        chat_id = update.message.chat_id
        message_id = update.message.message_id

        # ذخیره در کش
        message_buffer.append((chat_id, message_id))

        # زمان‌بندی پاک شدن خودکار
        await context.job_queue.run_once(
            delete_message, DELETE_DELAY, data={"chat_id": chat_id, "message_id": message_id}
        )

# تابع واقعی حذف پیام
async def delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning(f"خطا در حذف پیام {message_id}: {e}")

# دستور /clean
async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    # فقط ادمین‌ها
    member = await chat.get_member(user.id)
    if not (member.status in ["administrator", "creator"]):
        await update.message.reply_text("⛔ فقط ادمین‌ها می‌تونن از /clean استفاده کنن.")
        return

    try:
        n = int(context.args[0]) if context.args else 5
    except ValueError:
        n = 5

    deleted = 0
    # فقط پیام‌های همین چت
    to_delete = [msg for msg in list(message_buffer)[-n:] if msg[0] == chat.id]

    for chat_id, msg_id in to_delete:
        try:
            await context.bot.delete_message(chat_id, msg_id)
            deleted += 1
        except Exception as e:
            logger.warning(f"خطا در حذف پیام {msg_id}: {e}")

    await context.bot.send_message(chat.id, f"✅ {deleted} پیام آخر پاک شد.")

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
