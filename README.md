# Crypto Alert Telegram Bot (Binance, async, SQLite)

Бот присылает алерты по цене и по %-изменению за окно времени.
Реализовано на **Python 3.10+**, **aiogram v3**, **httpx**, **aiosqlite**.

## Команды
- `/start`, `/help` — краткая справка.
- `/price <SYMBOL>` — текущая цена (например: `/price BTCUSDT`).
- `/set <SYMBOL> <OP> <PRICE>` — ценовой алерт (одиночный). Примеры:
  - `/set BTCUSDT >= 65000`
  - `/set ETHUSDT <= 3000`
- `/set_pct <SYMBOL> <PERCENT> <WINDOW>` — алерт на %‑изменение за окно.
  - Окно: `15m`, `30m`, `1h`, `4h`, `1d`
  - Пример: `/set_pct BTCUSDT 5 1h` (±5% от цены за последний час)
- `/list` — показать активные алерты.
- `/delete <ID>` — удалить алерт.

После срабатывания алерт деактивируется (одиночный).

## Быстрый старт (локально)
1) Установите Python 3.10+.
2) В папке проекта:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env  # и вставьте токен Telegram-бота
   python app.py
   ```

## Docker
```bash
docker build -t crypto-alert-bot .
docker run --rm -it --env-file .env crypto-alert-bot
```

## Примечания
- Используется публичный API Binance (ключи не нужны).
- БД SQLite создаётся автоматически в `.data/bot.db`.
- Интервалы опроса и базовый URL настраиваются в `.env`.
- Код легко расширить: добавить EMA/RSI, уведомления в канал и т.д.
