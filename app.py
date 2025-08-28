from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import os
import asyncio

# =======  تنظیمات =========
TOKEN = os.environ.get("BOT_TOKEN")      # توکن ربات
APP_URL = os.environ.get("APP_URL")      # آدرس رندر مثل https://mybot.onrender.com

app = Flask(__name__)

# ======= ساخت اپلیکیشن تلگرام ========
application = ApplicationBuilder().token(TOKEN).build()

# ======= دستور /start =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات فعال است و پیام‌ها را پاک می‌کند.")

application.add_handler(CommandHandler("start", start))

# ======= دریافت پیام و حذف آن =======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            # حذف پیام ارسالی
            await update.message.delete()
            
            # پاسخ دادن به پیام (مثال: همان متن)
            await update.effective_chat.send_message(f"پیام شما دریافت شد: {update.message.text}")
        except Exception as e:
            print("خطا در حذف یا پاسخ:", e)

# همه پیام‌ها را مدیریت می‌کنیم
application.add_handler(MessageHandler(filters.ALL & (~filters.StatusUpdate.ALL), handle_message))

# ======= وبهوک =======
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, Bot(TOKEN))
    # اضافه کردن به صف اپلیکیشن
    asyncio.run(application.update_queue.put(update))
    return "ok"

# ======= Health Check برای Render =======
@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

# ======= اجرای برنامه =======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # پورت را از Render می‌گیریم
    app.run(host="0.0.0.0", port=port)
