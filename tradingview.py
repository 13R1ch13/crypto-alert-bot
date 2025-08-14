import logging
import time
from typing import Optional

import httpx

from config import TRADINGVIEW_API


# Простой клиент к публичному (полу‑официальному) API TradingView
class TradingViewClient:
    def __init__(self, base_url: str = TRADINGVIEW_API, timeout: float = 10.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            timeout=self.timeout, headers={"User-Agent": "crypto-alert-bot/1.0"}
        )

    async def close(self):
        await self._client.aclose()

    async def get_price(self, symbol: str) -> Optional[float]:
        """Возвращает текущую цену символа."""
        url = f"{self.base_url}/crypto/scan"
        payload = {
            "symbols": {"tickers": [f"BINANCE:{symbol.upper()}"], "query": {"types": []}},
            "columns": ["close"],
        }
        try:
            r = await self._client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            price = data["data"][0]["d"][0]
            return float(price)
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            logging.exception("get_price failed for %s: %s", symbol, e)
            return None

    async def get_klines(self, symbol: str, interval: str, limit: int = 2) -> Optional[list]:
        """Возвращает свечи (OHLC) для символа."""
        url = f"{self.base_url}/history"
        now = int(time.time())
        if interval.isdigit():
            step = int(interval) * 60
        elif interval.upper() == "D":
            step = 24 * 60 * 60
        else:
            step = 60 * 60
        params = {
            "symbol": f"BINANCE:{symbol.upper()}",
            "resolution": interval,
            "from": now - step * limit,
            "to": now,
        }
        try:
            r = await self._client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            t = data.get("t", [])
            o = data.get("o", [])
            h = data.get("h", [])
            l = data.get("l", [])
            c = data.get("c", [])
            klines = [
                [t[i] * 1000, o[i], h[i], l[i], c[i]]
                for i in range(min(len(t), len(o), len(h), len(l), len(c)))
            ]
            return klines[-limit:]
        except (httpx.HTTPError, KeyError, ValueError) as e:
            logging.exception("get_klines failed for %s %s: %s", symbol, interval, e)
            return None


WINDOW_TO_INTERVAL = {
    "15m": ("15", 15 * 60),
    "30m": ("30", 30 * 60),
    "1h": ("60", 60 * 60),
    "4h": ("240", 4 * 60 * 60),
    "1d": ("D", 24 * 60 * 60),
}


def parse_window(window: str):
    window = window.strip().lower()
    if window not in WINDOW_TO_INTERVAL:
        raise ValueError("Invalid window: use 15m, 30m, 1h, 4h, 1d")
    interval, seconds = WINDOW_TO_INTERVAL[window]
    return interval, seconds

