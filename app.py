import os
import asyncio
import logging
from collections import defaultdict, deque

from flask import Flask, request, abort
from asgiref.wsgi import WsgiToAsgi
import uvicorn

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("Env var TELEGRAM_TOKEN تنظیم نشده است.")

PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL")
if not PUBLIC_URL:
    raise RuntimeError("WEBHOOK_URL یا RENDER_EXTERNAL_URL تنظیم نیست.")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-this-to-a-long-random-string")

MSG_STORE: dict[int, deque[int]] = defaultdict(lambda: deque(maxlen=5000))

# ---------- Handlers ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.effective_message.reply_text("من فقط داخل گروه/سوپرگروه کار می‌کنم 🙂")
        return

    kb = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🧹 پاکسازی", callback_data="clean"),
            InlineKeyboardButton("🚪 خروج",    callback_data="leave"),
        ]]
    )
    await update.effective_message.reply_text("پنل مدیریت:", reply_markup=kb)

async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return
    if msg.chat.type in ("group", "supergroup"):
        MSG_STORE[msg.chat_id].append(msg.message_id)

async def _is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in ("administrator", "creator")

async def _bot_can_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    me = await context.bot.get_me()
    m = await context.bot.get_chat_member(chat_id, me.id)
    return (m.status in ("administrator", "creator")) and bool(getattr(m, "can_delete_messages", False))

async def _do_clean(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> int:
    ids = list(MSG_STORE.get(chat_id, []))
    if not ids:
        return 0
    deleted = 0
    for i in range(0, len(ids), 100):
        batch = ids[i:i+100]
        try:
            ok = await context.bot.delete_messages(chat_id=chat_id, message_ids=batch)
            if ok:
                deleted += len(batch)
        except Exception as e:
            logger.warning("delete_messages batch failed: %s", e)
    MSG_STORE[chat_id].clear()
    return deleted

async def clean_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ("group", "supergroup"):
        await update.effective_message.reply_text("این دستور فقط داخل گروه کار می‌کند.")
        return
    if not await _is_admin(context, chat.id, user.id):
        await update.effective_message.reply_text("⛔️ فقط ادمین می‌تواند پاکسازی کند.")
        return
    if not await _bot_can_delete(context, chat.id):
        await update.effective_message.reply_text("⛔️ ربات دسترسی حذف پیام ندارد. لطفاً حق «Delete messages» را بدهید.")
        return

    count = await _do_clean(chat.id, context)
    await update.effective_message.reply_text(f"✅ تلاش برای حذف {count} پیام (حداکثر ۴۸ ساعت اخیر).")

async def buttons_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = query.from_user.id

    if query.data == "clean":
        if not await _is_admin(context, chat_id, user_id):
            await query.edit_message_text("⛔️ فقط ادمین می‌تواند پاکسازی کند.")
            return
        if not await _bot_can_delete(context, chat_id):
            await query.edit_message_text("⛔️ ربات دسترسی حذف پیام ندارد.")
            return
        count = await _do_clean(chat_id, context)
        try:
            await query.edit_message_text(f"✅ تلاش برای حذف {count} پیام انجام شد.")
        except Exception:
            pass

    elif query.data == "leave":
        # فقط پاک کردن پیام منو، ربات از گروه خارج نمی‌شود
        try:
            await query.message.delete()
        except Exception:
            pass

async def welcome_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == (await context.bot.get_me()).id:
            await update.message.reply_text(
                "سلام! من اضافه شدم. لطفاً من را ادمین با دسترسی حذف پیام‌ها کنید تا پاکسازی کار کند ✅"
            )

# ---------- Application ----------
application = Application.builder().token(TOKEN).updater(None).build()
application.add_handler(CommandHandler("start", start_cmd))
application.add_handler(CommandHandler("clean", clean_cmd))
application.add_handler(CallbackQueryHandler(buttons_cb))
application.add_handler(MessageHandler(~filters.StatusUpdate.ALL, track_messages))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_bot))

# ---------- Flask ----------
flask_app = Flask(__name__)

@flask_app.post("/webhook")
async def webhook():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        abort(403)
    data = request.get_json(force=True, silent=True)
    if not data:
        return "no json", 400
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return "ok", 200

# مسیر ping برای UptimeRobot
@flask_app.get("/ping")
def ping():
    return "ok", 200

# ---------- Main ----------
async def main():
    webhook_url = f"{PUBLIC_URL.rstrip('/')}/webhook"
    await application.initialize()
    await application.bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )
    port = int(os.getenv("PORT", "10000"))
    server = uvicorn.Server(uvicorn.Config(WsgiToAsgi(flask_app), host="0.0.0.0", port=port))
    start_task = asyncio.create_task(application.start())
    try:
        await server.serve()
    finally:
        await application.stop()
        await application.shutdown()
        await start_task

if __name__ == "__main__":
    asyncio.run(main())
