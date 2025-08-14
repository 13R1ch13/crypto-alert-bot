import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import TELEGRAM_TOKEN, POLL_INTERVAL
from db import init_db, get_active_alerts, deactivate_alert
from handlers import router
from binance import BinanceClient, WINDOW_TO_INTERVAL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

async def poller(bot: Bot):
    client = BinanceClient()
    failed_deactivations = set()
    try:
        while True:
            try:
                alerts = await get_active_alerts()
            except Exception as e:
                logging.exception("get_active_alerts failed: %s", e)
                await asyncio.sleep(POLL_INTERVAL)
                continue

            prices_cache = {}
            klines_cache = {}

            for a in alerts:
                symbol = str(a.get("symbol", "")).upper()
                a_type = a.get("type")

                if a_type == "price":
                    if not symbol:
                        continue
                    if symbol not in prices_cache:
                        try:
                            prices_cache[symbol] = await client.get_price(symbol)
                        except Exception as e:
                            logging.warning("price failed for %s: %s", symbol, e)
                            continue

                    price = prices_cache[symbol]
                    op = a.get("op")
                    target = float(a.get("target", 0))
                    if (op == ">=" and price >= target) or (op == "<=" and price <= target):
                        text = f"🔔 #{a['id']} {symbol}: текущая {price:.8f} {op} {target}"
                        try:
                            await bot.send_message(a["chat_id"], text)
                        except Exception as e:
                            logging.warning("send_message failed: %s", e)
                        try:
                            await deactivate_alert(a["id"])
                        except Exception as e:
                            logging.warning("deactivate_alert failed for %s: %s", a["id"], e)
                            failed_deactivations.add(a["id"])

                elif a_type == "pct":
                    window = a.get("window_str")
                    interval = WINDOW_TO_INTERVAL.get(window, (None, None))[0]
                    if not symbol or not interval:
                        continue

                    key = (symbol, interval)
                    if key not in klines_cache:
                        try:
                            klines_cache[key] = await client.get_klines(symbol, interval, limit=2)
                        except Exception as e:
                            logging.warning("klines failed for %s %s: %s", symbol, interval, e)
                            continue

                    kl = klines_cache[key]
                    if len(kl) < 2:
                        continue

                    try:
                        prev_close = float(kl[-2][4])
                        last_close = float(kl[-1][4])
                    except Exception:
                        continue
                    if prev_close == 0:
                        continue

                    change_pct = (last_close - prev_close) / prev_close * 100.0
                    threshold = float(a.get("target", 0))
                    if abs(change_pct) >= threshold:
                        sign = "▲" if change_pct >= 0 else "▼"
                        text = (
                            f"🔔 #{a['id']} {symbol} {sign} {change_pct:.2f}% за {window}\n"
                            f"Цена: {last_close:.8f} (была {prev_close:.8f})"
                        )
                        try:
                            await bot.send_message(a["chat_id"], text)
                        except Exception as e:
                            logging.warning("send_message failed: %s", e)
                        try:
                            await deactivate_alert(a["id"])
                        except Exception as e:
                            logging.warning("deactivate_alert failed for %s: %s", a["id"], e)
                            failed_deactivations.add(a["id"])

            for alert_id in list(failed_deactivations):
                try:
                    await deactivate_alert(alert_id)
                except Exception as e:
                    logging.warning("deactivate_alert retry failed for %s: %s", alert_id, e)
                else:
                    failed_deactivations.discard(alert_id)

            await asyncio.sleep(POLL_INTERVAL)
    finally:
        try:
            await client.close()
        except Exception:
            pass

async def main():
    if not TELEGRAM_TOKEN or ":" not in TELEGRAM_TOKEN:
        raise SystemExit("TELEGRAM_TOKEN пустой или некорректный. Проверь .env у BotFather.")

    await init_db()

    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=None),
    )
    dp = Dispatcher()
    dp.include_router(router)

    asyncio.create_task(poller(bot))

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
