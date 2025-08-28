from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ====== تنظیمات ربات ======
TOKEN = "توکن_ربات_تو_اینجا"  # جایگزین با توکن خودت
app = Flask(__name__)
bot = Bot(token=TOKEN)

# ====== ساخت اپلیکیشن تلگرام ======
application = ApplicationBuilder().token(TOKEN).build()

# ====== دستورات ربات ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات با موفقیت فعال شد.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستورات موجود:\n/start - شروع ربات\n/help - راهنمایی\n/ping - بررسی سلامت\n/echo - تکرار پیام")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # متن بعد از /echo را دریافت می‌کند
    text_to_echo = " ".join(context.args)
    if not text_to_echo:
        await update.message.reply_text("لطفاً بعد از /echo چیزی تایپ کن تا تکرار شود.")
    else:
        await update.message.reply_text(text_to_echo)

# افزودن handler ها
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("ping", ping))
application.add_handler(CommandHandler("echo", echo))

# ====== مسیر webhook ======
@app.route("/webhook/<token>", methods=["POST"])
async def webhook(token):
    if token != TOKEN:
        return "Unauthorized", 403
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "ok"

# ====== مسیر Health Check ======
@app.route("/")
def index():
    return "ربات آماده است!"

# ====== اجرای محلی (اختیاری) ======
if __name__ == "__main__":
    import asyncio
    asyncio.run(app.run(host="0.0.0.0", port=5000))
