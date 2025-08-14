import os
import logging
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# POLL_INTERVAL should be an integer number of seconds
_poll_interval = os.getenv("POLL_INTERVAL", "15")
try:
    POLL_INTERVAL = int(_poll_interval)
except ValueError:
    logging.error(
        "Invalid POLL_INTERVAL '%s'. Expected an integer. Using default of 15 seconds.",
        _poll_interval,
    )
    POLL_INTERVAL = 15

DB_PATH = os.getenv("DB_PATH", ".data/bot.db")
TRADINGVIEW_API = os.getenv("TRADINGVIEW_API", "https://scanner.tradingview.com")
