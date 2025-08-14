import logging
import httpx
from typing import Optional
from config import BINANCE_API

# Простой клиент к публичному API Binance
class BinanceClient:
    def __init__(self, base_url: str = BINANCE_API, timeout: float = 10.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=self.timeout, headers={"User-Agent": "crypto-alert-bot/1.0"})

    async def close(self):
        await self._client.aclose()

    async def get_price(self, symbol: str) -> Optional[float]:
        url = f"{self.base_url}/api/v3/ticker/price"
        try:
            r = await self._client.get(url, params={"symbol": symbol.upper()})
            r.raise_for_status()
            data = r.json()
            return float(data["price"])
        except httpx.HTTPError as e:
            logging.exception("get_price failed for %s: %s", symbol, e)
            return None

    async def get_klines(self, symbol: str, interval: str, limit: int = 2) -> Optional[list]:
        url = f"{self.base_url}/api/v3/klines"
        try:
            r = await self._client.get(url, params={"symbol": symbol.upper(), "interval": interval, "limit": limit})
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            logging.exception("get_klines failed for %s %s: %s", symbol, interval, e)
            return None

WINDOW_TO_INTERVAL = {
    "15m": ("15m", 15*60),
    "30m": ("30m", 30*60),
    "1h":  ("1h",  60*60),
    "4h":  ("4h",  4*60*60),
    "1d":  ("1d",  24*60*60),
}

def parse_window(window: str):
    window = window.strip().lower()
    if window not in WINDOW_TO_INTERVAL:
        raise ValueError("Invalid window: use 15m, 30m, 1h, 4h, or 1d")
    interval, seconds = WINDOW_TO_INTERVAL[window]
    return interval, seconds
