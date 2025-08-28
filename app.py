import os
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CallbackQueryHandler

TOKEN = os.environ.get("TELEGRAM_TOKEN")
APP_URL = os.environ.get("APP_URL")  # https://yourapp.onrender.com

flask_app = Flask(__name__)
bot = Bot(token=TOKEN)

# ------------------------------
# Inline Keyboard
# ------------------------------
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("پاکسازی گروه", callback_data="clean")],
    [InlineKeyboardButton("خروج ربات", callback_data="leave")]
])

# ------------------------------
# Handlers
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات فعال شد!", reply_markup=keyboard)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if query.data == "clean":
        try:
            # پاکسازی 100 پیام اخیر گروه
            messages = await context.bot.get_chat(chat_id).get_history(limit=100)
            for msg in messages:
                try:
                    await context.bot.delete_message(chat_id, msg.message_id)
                except:
                    pass
            await query.edit_message_text("تمام پیام‌های گروه پاک شد!")
        except Exception as e:
            await query.edit_message_text(f"خطا در پاکسازی: {e}")

    elif query.data == "leave":
        try:
            await context.bot.send_message(chat_id, "ربات گروه را ترک می‌کند.")
            await context.bot.leave_chat(chat_id)
        except Exception as e:
            await query.edit_message_text(f"خطا در خروج: {e}")

# ------------------------------
# Telegram Application
# ------------------------------
app_builder = ApplicationBuilder().token(TOKEN).build()
app_builder.add_handler(CallbackQueryHandler(button))

# ------------------------------
# Flask Webhook
# ------------------------------
@flask_app.route("/")
def index():
    return "Bot is running!"

@flask_app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    app_builder.update_queue.put(update)
    return "ok"

# Set webhook on startup
@app_builder.run_async
async def set_webhook():
    await bot.set_webhook(f"{APP_URL}/webhook/{TOKEN}")
