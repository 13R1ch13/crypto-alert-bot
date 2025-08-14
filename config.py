import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))
DB_PATH = os.getenv("DB_PATH", "data/bot.db")
BINANCE_API = os.getenv("BINANCE_API", "https://api.binance.com")
