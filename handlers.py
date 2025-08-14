from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db import add_price_alert, add_pct_alert, list_alerts, delete_alert
from binance import parse_window
from binance import BinanceClient
import re
import asyncio

router = Router()

SYMBOL_RE = re.compile(r'^[A-Z0-9]{5,15}$')

HELP_TEXT = (
    "Привет! Я крипто‑алерт бот. Доступные команды:\n\n"
    "/price <SYMBOL> — текущая цена (пример: /price BTCUSDT)\n"
    "/set <SYMBOL> <OP> <PRICE> — ценовой алерт (пример: /set BTCUSDT >= 65000)\n"
    "/set_pct <SYMBOL> <PERCENT> <WINDOW> — алерт на % за окно (пример: /set_pct BTCUSDT 5 1h)\n"
    "/list — список ваших алертов\n"
    "/delete <ID> — удалить алерт"
)

@router.message(Command("start"))
@router.message(Command("help"))
async def cmd_start(message: Message):
    await message.answer(HELP_TEXT)

@router.message(Command("price"))
async def cmd_price(message: Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("Использование: /price <SYMBOL> (например: /price BTCUSDT)")
        return
    symbol = parts[1].upper()
    if not SYMBOL_RE.match(symbol):
        await message.answer("Некорректный символ. Пример: BTCUSDT")
        return
    client = BinanceClient()
    try:
        price = await client.get_price(symbol)
        if price is None:
            await message.answer("Ошибка получения цены")
        else:
            await message.answer(f"{symbol}: {price:.8f}")
    except Exception as e:
        await message.answer(f"Ошибка получения цены: {e}")
    finally:
        await client.close()

@router.message(Command("set"))
async def cmd_set(message: Message):
    # /set BTCUSDT >= 65000
    parts = message.text.strip().split()
    if len(parts) != 4:
        await message.answer("Формат: /set <SYMBOL> <OP> <PRICE>\nПример: /set BTCUSDT >= 65000")
        return
    symbol, op, price = parts[1].upper(), parts[2], parts[3]
    if not SYMBOL_RE.match(symbol):
        await message.answer("Некорректный символ. Пример: BTCUSDT")
        return
    if op not in (">=", "<="):
        await message.answer("OP должен быть '>=' или '<='")
        return
    try:
        target = float(price.replace(',', '.'))
    except ValueError:
        await message.answer("PRICE должен быть числом")
        return

    alert_id = await add_price_alert(message.from_user.id, message.chat.id, symbol, op, target)
    await message.answer(f"✅ Алерт #{alert_id} создан: {symbol} {op} {target}")

@router.message(Command("set_pct"))
async def cmd_set_pct(message: Message):
    # /set_pct BTCUSDT 5 1h
    parts = message.text.strip().split()
    if len(parts) != 4:
        await message.answer("Формат: /set_pct <SYMBOL> <PERCENT> <WINDOW>\nПример: /set_pct BTCUSDT 5 1h")
        return
    symbol, pct_str, window = parts[1].upper(), parts[2], parts[3]
    if not SYMBOL_RE.match(symbol):
        await message.answer("Некорректный символ. Пример: BTCUSDT")
        return
    try:
        percent = float(pct_str.replace(',', '.'))
    except ValueError:
        await message.answer("PERCENT должен быть числом")
        return
    if percent <= 0:
        await message.answer("PERCENT должен быть положительным")
        return
    try:
        interval, seconds = parse_window(window)
    except ValueError as e:
        await message.answer(str(e))
        return

    alert_id = await add_pct_alert(message.from_user.id, message.chat.id, symbol, percent, window, seconds)
    await message.answer(f"✅ Алерт #{alert_id} создан: {symbol} ±{percent}% за {window}")

@router.message(Command("list"))
async def cmd_list(message: Message):
    rows = await list_alerts(message.from_user.id)
    if not rows:
        await message.answer("У вас нет алертов.")
        return
    lines = []
    for r in rows:
        if r['type'] == 'price':
            lines.append(f"#{r['id']}: {r['symbol']} {r['op']} {r['target']}  | active={r['active']}")
        else:
            lines.append(f"#{r['id']}: {r['symbol']} ±{r['target']}% / {r['window_str']} | active={r['active']}")
    await message.answer("\n".join(lines))

@router.message(Command("delete"))
async def cmd_delete(message: Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("Формат: /delete <ID>")
        return
    try:
        alert_id = int(parts[1])
    except ValueError:
        await message.answer("ID должен быть числом")
        return
    ok = await delete_alert(alert_id, message.from_user.id)
    if ok:
        await message.answer(f"🗑️ Алерт #{alert_id} удалён")
    else:
        await message.answer("Не найден алерт с таким ID (или он не ваш).")
