import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from config import TELEGRAM_TOKEN, POLL_INTERVAL
from db import init_db, get_active_alerts, deactivate_alert
from handlers import router
from binance import BinanceClient, WINDOW_TO_INTERVAL

async def poller(bot: Bot):
    client = BinanceClient()
    try:
        while True:
            alerts = await get_active_alerts()
            # Группируем по символу и типу окна, чтобы меньше дергать API
            # Для price получаем цену 1 раз на символ, для pct получаем 2 свечи на интервал.
            prices_cache = {}
            klines_cache = {}

            for a in alerts:
                symbol = a['symbol'].upper()
                if a['type'] == 'price':
                    if symbol not in prices_cache:
                        try:
                            prices_cache[symbol] = await client.get_price(symbol)
                        except Exception as e:
                            # Лог ошибок можно добавить
                            continue
                    price = prices_cache[symbol]
                    op = a['op']
                    target = float(a['target'])
                    triggered = (price >= target) if op == '>=' else (price <= target)
                    if triggered:
                        text = f"🔔 #{a['id']} {symbol}: текущая {price:.8f} {op} {target}"
                        await bot.send_message(a['chat_id'], text)
                        await deactivate_alert(a['id'])

                elif a['type'] == 'pct':
                    window = a['window_str']
                    interval = WINDOW_TO_INTERVAL.get(window, (None, None))[0]
                    if interval is None:
                        continue
                    key = (symbol, interval)
                    if key not in klines_cache:
                        try:
                            # Берём 2 последних свечи данного интервала
                            kl = await client.get_klines(symbol, interval, limit=2)
                            klines_cache[key] = kl
                        except Exception as e:
                            continue
                    kl = klines_cache[key]
                    if len(kl) < 2:
                        continue
                    prev_close = float(kl[-2][4])  # close предыдущей свечи
                    last_close = float(kl[-1][4])  # close последней свечи
                    if prev_close == 0:
                        continue
                    change_pct = (last_close - prev_close) / prev_close * 100.0
                    threshold = float(a['target'])
                    if abs(change_pct) >= threshold:
                        sign = "▲" if change_pct >= 0 else "▼"
                        text = (
                            f"🔔 #{a['id']} {symbol} {sign} {change_pct:.2f}% за {window}\n"
                            f"Цена: {last_close:.8f} (была {prev_close:.8f})"
                        )
                        await bot.send_message(a['chat_id'], text)
                        await deactivate_alert(a['id'])

            await asyncio.sleep(POLL_INTERVAL)
    finally:
        await client.close()

async def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("TELEGRAM_TOKEN пуст. Укажите токен в .env")
    await init_db()

    bot = Bot(token=TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(router)

    # Стартуем фоновый поллер
    asyncio.create_task(poller(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
