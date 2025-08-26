# Telegram Echo Bot (بدون render.yaml)

یک ربات ساده تلگرام با Python و [python-telegram-bot](https://python-telegram-bot.org).

## 🚀 دیپلوی روی Render (وب‌سرویس معمولی)
1. این Repo را روی GitHub قرار دهید.
2. در Render → New + → Web Service → Repo را انتخاب کنید.
3. تنظیمات:
   - Environment: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: python app.py
4. Env Vars را در Settings اضافه کنید:
   - `TELEGRAM_TOKEN` = توکن BotFather
   - `PUBLIC_URL` = آدرس پابلیک سرویس (مثلاً https://telegram-echo-bot.onrender.com)
   - `WEBHOOK_SECRET` = یک رشته امن دلخواه
5. Redeploy کنید.
