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

# Render خودش RENDER_EXTERNAL_URL رو می‌ذاره. اگر محض احتیاط خودت URL داری، توی WEBHOOK_URL بذار.
PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL")
if not PUBLIC_URL:
    raise RuntimeError("WEBHOOK_URL یا RENDER_EXTERNAL_URL تنظیم نیست.")

# برای امنیت وبهوک (هدر X-Telegram-Bot-Api-Secret-Token)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-this-to-a-long-random-string")

# حافظه‌ی ساده برای ذخیره‌ی شناسه‌ی پیام‌ها (فقط پیام‌هایی که ربات دیده)
# محدود به 5000 پیام آخر هر گروه
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
    """هر پیامی که می‌رسه IDشو ذخیره می‌کنیم تا بعداً پاک بشه (تا سقف ۴۸ ساعت اخیر)."""
    msg = update.effective_message
    if not msg:
        return
    # فقط چت‌های گروهی
    if msg.chat.type in ("group", "supergroup"):
        MSG_STORE[msg.chat_id].append(msg.message_id)

async def _is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in ("administrator", "creator")

async def _bot_can_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    me = await context.bot.get_me()
    m = await context.bot.get_chat_member(chat_id, me.id)
    # باید ادمین باشه و حق حذف پیام داشته باشه
    return (m.status in ("administrator", "creator")) and bool(getattr(m, "can_delete_messages", False))

async def _do_clean(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> int:
    """حذف دسته‌ای پیام‌ها؛ تلگرام حداکثر ۱۰۰ تا در هر فراخوانی و تا پیام‌های <=۴۸ ساعت اخیر."""
    ids = list(MSG_STORE.get(chat_id, []))
    if not ids:
        return 0

    deleted = 0
    # در دسته‌های ۱۰۰تایی
    for i in range(0, len(ids), 100):
        batch = ids[i:i+100]
        try:
            ok = await context.bot.delete_messages(chat_id=chat_id, message_ids=batch)
            if ok:
                deleted += len(batch)
        except Exception as e:
            logger.warning("delete_messages batch failed: %s", e)

    # بعد از تلاش برای حذف، لیست رو خالی می‌کنیم
    MSG_STORE[chat_id].clear()
    return deleted

async def clean_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """برای دستور /clean"""
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
    await update.effective_message.reply_text(f"✅ تلاش برای حذف {count} پیام (حداکثر ۴۸ ساعت اخیر و پیام‌هایی که ربات دیده).")

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
            await query.edit_message_text("⛔️ ربات دسترسی حذف پیام ندارد. لطفاً حق «Delete messages» را بدهید.")
            return
        count = await _do_clean(chat_id, context)
        try:
            await query.edit_message_text(f"✅ تلاش برای حذف {count} پیام انجام شد.")
        except Exception:
            # اگر پیام خودِ کیبورد هم حذف شده بود، مشکلی نیست
            pass

    elif query.data == "leave":
        if not await _is_admin(context, chat_id, user_id):
            await query.edit_message_text("⛔️ فقط ادمین می‌تواند ربات را خارج کند.")
            return
        try:
            await query.edit_message_text("👋 خداحافظ!")
        except Exception:
            pass
        try:
            await context.bot.leave_chat(chat_id)
        except Exception as e:
            logger.error("leave_chat failed: %s", e)

# ---------- Build PTB Application (بدون Updater) ----------
application = Application.builder().token(TOKEN).updater(None).build()
application.add_handler(CommandHandler("start", start_cmd))
application.add_handler(CommandHandler("clean", clean_cmd))
application.add_handler(CallbackQueryHandler(buttons_cb))
# همه‌ی پیام‌ها بجز وضعیت‌های سیستمی (join/left و …) رو ذخیره کن
application.add_handler(MessageHandler(~filters.StatusUpdate.ALL, track_messages))

# ---------- Flask Webhook ----------
flask_app = Flask(__name__)

@flask_app.post("/webhook")
async def webhook():
    # امن‌سازی با secret token
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        abort(403)
    data = request.get_json(force=True, silent=True)
    if not data:
        return "no json", 400
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return "ok", 200

async def main():
    # ست‌کردن وبهوک در تلگرام
    webhook_url = f"{PUBLIC_URL.rstrip('/')}/webhook"
    await application.initialize()
    await application.bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )
    # اجرای همزمان PTB و وب‌سرور
    port = int(os.getenv("PORT", "10000"))
    server = uvicorn.Server(uvicorn.Config(WsgiToAsgi(flask_app), host="0.0.0.0", port=port, log_level="inf
