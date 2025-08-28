from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler

# توکن ربات خودتون
TOKEN = "8344618608:AAHHSriiACSEQZ3TzXmfW8rbx0HAdGPGpp4"

bot = Bot(token=TOKEN)
app = Flask(__name__)

# ساخت Application تلگرام
application = ApplicationBuilder().token(TOKEN).build()

# دستور /start
async def start(update: Update, context):
    await update.message.reply_text("سلام! ربات شما آماده است.")

# دستور /help
async def help_command(update: Update, context):
    await update.message.reply_text(
        "دستورات موجود:\n"
        "/start - شروع ربات\n"
        "/help - راهنمای دستورات\n"
        "/echo - تکرار پیغام شما"
    )

# دستور /echo
async def echo(update: Update, context):
    if context.args:
        text = " ".join(context.args)
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("لطفا متنی برای تکرار ارسال کنید. مثال:\n/echo سلام")

# اضافه کردن دستورها به ربات
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("echo", echo))

# وبهوک سینک برای Flask
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.process_update(update)  # پردازش آپدیت
    return "ok"

# روت ساده برای تست
@app.route("/")
def index():
    return "ربات فعال است!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
