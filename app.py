import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatMemberStatus

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret")
APP_URL = os.getenv("APP_URL")  # مثلا https://mybot.onrender.com

# ---------------- Flask ----------------
flask_app = Flask(__name__)

@flask_app.get("/ping")
def ping():
    return "ok", 200

@flask_app.post(f"/webhook/{WEBHOOK_SECRET}")
async def webhook() -> tuple[str, int]:
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return "ok", 200

# ---------------- Bot Logic ----------------
message_store = {}

# چک کردن ادمین بودن کاربر
async def _is_admin(context: CallbackContext, chat_id: int, user_id: int) -> bool:
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

# چک کردن دسترسی حذف برای ربات
async def _bot_can_delete(context: CallbackContext, chat_id: int) -> bool:
    me = await context.bot.get_me()
    member = await context.bot.get_chat_member(chat_id, me.id)
    return member.can_delete_messages

# ذخیره پیام‌ها
async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg_id = update.effective_message.id
    message_store.setdefault(chat_id, set()).add(msg_id)

# پاکسازی پیام‌ها
async def _do_clean(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> int:
    ids = list(message_store.get(chat_id, []))
    count = 0
    for mid in ids:
        try:
            await context.bot.delete_message(chat_id, mid)
            count += 1
        except:
            pass
    message_store[chat_id] = set()
    return count

# ---------------- Commands ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("🧹 پاکسازی", callback_data="clean"),
        InlineKeyboardButton("❌ خروج", callback_data="exit")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent = await update.effective_message.reply_text(
        "👋 سلام! این پنل مدیریت ربات است:", reply_markup=reply_markup
    )
    await asyncio.sleep(5)
    await sent.delete()

async def clean_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ("group", "supergroup"):
        sent = await update.effective_message.reply_text("⛔️ این دستور فقط داخل گروه کار می‌کند.")
        await asyncio.sleep(5)
        await sent.delete()
        return

    if not await _is_admin(context, chat.id, user.id):
        sent = await update.effective_message.reply_text("⛔️ فقط ادمین می‌تواند پاکسازی کند.")
        await asyncio.sleep(5)
        await sent.delete()
        return

    if not await _bot_can_delete(context, chat.id):
        sent = await update.effective_message.reply_text("⛔️ ربات دسترسی حذف پیام ندارد.")
        await asyncio.sleep(5)
        await sent.delete()
        return

    count = await _do_clean(chat.id, context)
    sent = await update.effective_message.reply_text(f"✅ {count} پیام پاک شد.")
    await asyncio.sleep(5)
    await sent.delete()

async def buttons_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "clean":
        await clean_cmd(update, context)
    elif query.data == "exit":
        sent = await query.message.reply_text("❌ خروج از پنل مدیریت.")
        await asyncio.sleep(5)
        await sent.delete()

async def welcome_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for m in update.message.new_chat_members:
        if m.id == context.bot.id:
            sent = await update.effective_message.reply_text(
                "✅ ربات افزوده شد! لطفاً دسترسی «Delete messages» بدهید."
            )
            await asyncio.sleep(5)
            await sent.delete()

# ---------------- Application ----------------
application = Application.builder().token(TOKEN).updater(None).build()

# دستورات بدون اسلش
application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^start$"), start_cmd))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^clean$"), clean_cmd))

# دکمه‌ها
application.add_handler(CallbackQueryHandler(buttons_cb))
# ذخیره پیام‌ها
application.add_handler(MessageHandler(~filters.StatusUpdate.ALL, track_messages))
# خوش‌آمدگویی
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_bot))

# ---------------- Main ----------------
async def main():
    if not TOKEN:
        raise RuntimeError("Env var TELEGRAM_TOKEN تنظیم نشده است.")
    if not APP_URL:
        raise RuntimeError("Env var APP_URL تنظیم نشده است.")

    await application.bot.set_webhook(f"{APP_URL}/webhook/{WEBHOOK_SECRET}")
    await application.initialize()
    await application.start()
    print("Bot started with webhook:", f"{APP_URL}/webhook/{WEBHOOK_SECRET}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
