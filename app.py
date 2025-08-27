import logging
import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# -----------------------------
# لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# توکن و تنظیمات محیطی
TOKEN = os.getenv("TELEGRAM_TOKEN")
PUBLIC_URL = os.getenv("PUBLIC_URL")  # آدرس پابلیک Render
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")

if not TOKEN or not PUBLIC_URL:
    raise RuntimeError("❌ باید متغیرهای محیطی TELEGRAM_TOKEN و PUBLIC_URL تنظیم بشن.")

# -----------------------------
# اپ Flask برای وبهوک
app = Flask(__name__)

# اپ تلگرام
application = Application.builder().token(TOKEN).build()

# -----------------------------
# /start → نمایش دکمه‌ها
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🧹 پاکسازی", callback_data="clean"),
            InlineKeyboardButton("🚪 خروج", callback_data="leave"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ بات فعال شد. یکی از گزینه‌ها رو انتخاب کن:", reply_markup=reply_markup)


# -----------------------------
# هندلر دکمه‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "clean":
        chat = update.effective_chat
        n = 10  # تعداد پیام‌هایی که میخوای پاک بشه
        current_id = query.message.message_id
        deleted = 0
        for i in range(n + 1):
            try:
                await context.bot.delete_message(chat.id, current_id - i)
                deleted += 1
            except Exception as e:
                logger.warning(f"خطا در حذف پیام {current_id - i}: {e}")

        await context.bot.send_message(chat.id, f"🧹 {deleted} پیام آخر پاک شد.")

    elif query.data == "leave":
        chat = update.effective_chat
        await context.bot.send_message(chat.id, "🚪 بات در حال خروج است...")
        await context.bot.leave_chat(chat.id)


# -----------------------------
# اضافه کردن هندلرها
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))


# -----------------------------
# مسیر وبهوک
@app.route(f"/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200


# -----------------------------
# راه‌اندازی وبهوک هنگام اجرای روی Render
@app.before_first_request
def set_webhook():
    url = f"{PUBLIC_URL}/{WEBHOOK_SECRET}"
    logger.info(f"تنظیم وبهوک روی: {url}")
    application.bot.set_webhook(url)


# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
