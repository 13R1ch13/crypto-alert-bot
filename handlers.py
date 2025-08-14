from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db import add_price_alert, add_pct_alert, list_alerts, delete_alert
from tradingview import parse_window
from tradingview import TradingViewClient
import re
import asyncio

router = Router()

SYMBOL_RE = re.compile(r'^[A-Z0-9]{5,15}$')

HELP_TEXT = (
    "Hello! I'm a crypto alert bot. Available commands:\n\n"
    "/price <SYMBOL> — current price (e.g. /price BTCUSDT)\n"
    "/set <SYMBOL> <OP> <PRICE> — price alert (e.g. /set BTCUSDT >= 65000)\n"
    "/set_pct <SYMBOL> <PERCENT> <WINDOW> — percent change alert (e.g. /set_pct BTCUSDT 5 1h)\n"
    "/list — list your alerts\n"
    "/delete <ID> — delete an alert"
)

@router.message(Command("start"))
@router.message(Command("help"))
async def cmd_start(message: Message):
    await message.answer(HELP_TEXT)

@router.message(Command("price"))
async def cmd_price(message: Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("Usage: /price <SYMBOL> (e.g. /price BTCUSDT)")
        return
    symbol = parts[1].upper()
    if not SYMBOL_RE.match(symbol):
        await message.answer("Invalid symbol. Example: BTCUSDT")
        return
    client = TradingViewClient()
    try:
        price = await client.get_price(symbol)
        if price is None:
            await message.answer("Error fetching price")
        else:
            await message.answer(f"{symbol}: {price:.8f}")
    except Exception as e:
        await message.answer(f"Error fetching price: {e}")
    finally:
        await client.close()

@router.message(Command("set"))
async def cmd_set(message: Message):
    # /set BTCUSDT >= 65000
    parts = message.text.strip().split()
    if len(parts) != 4:
        await message.answer("Format: /set <SYMBOL> <OP> <PRICE>\nExample: /set BTCUSDT >= 65000")
        return
    symbol, op, price = parts[1].upper(), parts[2], parts[3]
    if not SYMBOL_RE.match(symbol):
        await message.answer("Invalid symbol. Example: BTCUSDT")
        return
    if op not in (">=", "<="):
        await message.answer("OP must be '>=' or '<='")
        return
    try:
        target = float(price.replace(',', '.'))
    except ValueError:
        await message.answer("PRICE must be a number")
        return

    alert_id = await add_price_alert(message.from_user.id, message.chat.id, symbol, op, target)
    await message.answer(f"✅ Alert #{alert_id} created: {symbol} {op} {target}")

@router.message(Command("set_pct"))
async def cmd_set_pct(message: Message):
    # /set_pct BTCUSDT 5 1h
    parts = message.text.strip().split()
    if len(parts) != 4:
        await message.answer("Format: /set_pct <SYMBOL> <PERCENT> <WINDOW>\nExample: /set_pct BTCUSDT 5 1h")
        return
    symbol, pct_str, window = parts[1].upper(), parts[2], parts[3]
    if not SYMBOL_RE.match(symbol):
        await message.answer("Invalid symbol. Example: BTCUSDT")
        return
    try:
        percent = float(pct_str.replace(',', '.'))
    except ValueError:
        await message.answer("PERCENT must be a number")
        return
    if percent <= 0:
        await message.answer("PERCENT must be positive")
        return
    try:
        interval, seconds = parse_window(window)
    except ValueError as e:
        await message.answer(str(e))
        return

    alert_id = await add_pct_alert(message.from_user.id, message.chat.id, symbol, percent, window, seconds)
    await message.answer(f"✅ Alert #{alert_id} created: {symbol} ±{percent}% over {window}")

@router.message(Command("list"))
async def cmd_list(message: Message):
    rows = await list_alerts(message.from_user.id)
    if not rows:
        await message.answer("You have no alerts.")
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
        await message.answer("Format: /delete <ID>")
        return
    try:
        alert_id = int(parts[1])
    except ValueError:
        await message.answer("ID must be a number")
        return
    ok = await delete_alert(alert_id, message.from_user.id)
    if ok:
        await message.answer(f"🗑️ Alert #{alert_id} deleted")
    else:
        await message.answer("No alert found with that ID (or it's not yours).")
