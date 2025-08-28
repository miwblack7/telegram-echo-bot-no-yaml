import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot, ChatMember, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, ChatMemberHandler
)

# Flask app
app = Flask(__name__)

# دریافت توکن
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Env var TELEGRAM_TOKEN تنظیم نشده است.")

bot = Bot(token=TELEGRAM_TOKEN)
app_builder = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# دستور start (بدون اسلش)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات آنلاین است.")

# دستور clean (پاکسازی پیام‌های گروه)
async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("این دستور فقط در گروه قابل استفاده است.")
        return

    # پاک کردن پیام‌های گروه (به تعداد محدود، به دلیل محدودیت Telegram)
    messages = await context.bot.get_chat_history(chat.id, limit=100)
    for msg in messages:
        try:
            await msg.delete()
        except:
            pass
    await update.message.reply_text("پیام‌های گروه پاک شد!")

# اضافه شدن ربات به گروه → گرفتن ادمین کامل
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if result.new_chat_member.user.id == bot.id:
        await bot.promote_chat_member(
            chat_id=result.chat.id,
            user_id=bot.id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_promote_members=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True,
            is_anonymous=False
        )

# اضافه کردن handler ها
app_builder.add_handler(CommandHandler("start", start))
app_builder.add_handler(CommandHandler("clean", clean))
app_builder.add_handler(ChatMemberHandler(new_member, ChatMemberHandler.MY_CHAT_MEMBER))

# وبهوک
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(app_builder.update_queue.put(update))
    return "OK"

# Health Check
@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
