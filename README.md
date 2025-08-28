# Telegram Clean Bot

ربات تلگرام با وبهوک و Flask برای پاکسازی پیام‌ها

## Environment Variables

- TELEGRAM_TOKEN: توکن ربات تلگرام
- WEBHOOK_SECRET: یک رشته دلخواه برای امنیت وبهوک
- APP_URL: آدرس سرویس Render (مثلا https://mybot.onrender.com)

## Deploy on Render

Start Command:
```
gunicorn app:flask_app --preload --workers=4 --threads=8 --bind=0.0.0.0:$PORT
```

## Health Check
برای تست سلامت سرویس:
```
https://your-bot-name.onrender.com/ping
```
