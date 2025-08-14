# Crypto Alert Telegram Bot (Binance, async, SQLite)

The bot sends alerts for price moves and percent change over a time window.
Built with **Python 3.10+**, **aiogram v3**, **httpx**, **aiosqlite**.

## Commands
- `/start`, `/help` — short help.
- `/price <SYMBOL>` — current price (example: `/price BTCUSDT`).
- `/set <SYMBOL> <OP> <PRICE>` — price alert (single shot). Examples:
  - `/set BTCUSDT >= 65000`
  - `/set ETHUSDT <= 3000`
- `/set_pct <SYMBOL> <PERCENT> <WINDOW>` — percent change alert over a window.
  - Windows: `15m`, `30m`, `1h`, `4h`, `1d`
  - Example: `/set_pct BTCUSDT 5 1h` (±5% from the price over the last hour)
- `/list` — show active alerts.
- `/delete <ID>` — delete an alert.

Alerts deactivate after triggering (single shot).

## Quick start (local)
1. Install Python 3.10+.
2. In the project folder:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env  # paste your Telegram bot token
   python app.py
   ```

## Docker
```bash
docker build -t crypto-alert-bot .
docker run --rm -it --env-file .env crypto-alert-bot
```

## Notes
- Uses the public Binance API (no keys required).
- The SQLite database is created automatically at `.data/bot.db`.
- Polling intervals and the base URL are configured in `.env`.
- The code is easy to extend: add EMA/RSI, channel notifications, etc.

