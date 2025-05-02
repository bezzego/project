# config.py
import os
from dotenv import load_dotenv

# если .env лежит рядом — подгрузим его
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
YOOMONEY_TOKEN = os.getenv("YOOMONEY_TOKEN")
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/subscriptions.db")
SUB_PRICE = float(os.getenv("SUB_PRICE", "0"))
SUB_DURATION_DAYS = int(os.getenv("SUB_DURATION_DAYS", "0"))

# Интервал опроса платежей (в секундах)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

# Простейшие проверки
for name, val in [
    ("BOT_TOKEN", BOT_TOKEN),
    ("YOOMONEY_TOKEN", YOOMONEY_TOKEN),
    ("YOOMONEY_WALLET", YOOMONEY_WALLET),
    ("CHANNEL_ID", CHANNEL_ID),
]:
    if not val:
        raise RuntimeError(f"Не задана переменная {name} в окружении")
