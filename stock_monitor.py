"""
Stock monitor.

Runs continuously as a systemd service (see stock_monitor.service — started
once, kept alive with `Restart=always`). While the NSE market is open, it
checks every watched stock's live price every 5 minutes, and sends a
Telegram message the first time a stock's price reaches its Target.

This is a standalone script, separate from the FastAPI app, but it reuses
the app's settings and its shared Yahoo Finance lookup (fetch_cmp).
"""

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import pandas as pd

from app.core.config import get_settings
from app.infrastructure.sources.yfinance_client import fetch_cmp

settings = get_settings()

# Same file + sheet that excel_source.py's Breakout sheet uses.
WATCHLIST_FILE = "tests/My-watchlist-stocks.xlsx"
SHEET_NAME = "Breakout Stocks CMP"

IST = ZoneInfo("Asia/Kolkata")


def market_is_open() -> bool:
    """NSE regular trading hours: Monday-Friday, 9:15-15:30 IST."""
    now = datetime.now(IST)

    if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False

    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def get_watchlist() -> dict[str, float]:
    """Read {symbol: target_price} from the watchlist's Breakout sheet."""
    df = pd.read_excel(WATCHLIST_FILE, sheet_name=SHEET_NAME, header=1)

    targets: dict[str, float] = {}
    for _, row in df.iterrows():
        symbol = str(row["Symbol"]).strip().upper()
        target = row["Target"]
        if symbol and pd.notna(target):
            targets[symbol] = float(target)
    return targets


def get_latest_prices(symbols: list[str]) -> dict[str, float]:
    """Fetch the current price for each symbol (skips any that fail to fetch)."""
    prices: dict[str, float] = {}
    for symbol in symbols:
        info = fetch_cmp(symbol)
        if info is None:
            continue

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price is not None:
            prices[symbol] = price
    return prices


def breakout_detected(price: float, target: float) -> bool:
    """Has the price reached/crossed the target?"""
    return price >= target


async def send_telegram_notification(breakouts: list[tuple[str, float, float]]) -> None:
    """Send one Telegram message listing every stock that crossed its target this cycle."""
    if not breakouts:
        return

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        symbols = [symbol for symbol, _, _ in breakouts]
        print(f"Telegram not configured — skipping alert for {symbols}")
        return

    lines = [
        f"{symbol} crossed its target! CMP: {price}, Target: {target}"
        for symbol, price, target in breakouts
    ]
    text = "\n".join(lines)
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"

    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, data={"chat_id": settings.telegram_chat_id, "text": text})
        except Exception as err:
            print(f"Could not send Telegram notification: {err}")


async def strategy_loop() -> None:
    # Remembers which symbols are currently above target, so we notify once
    # per crossing (not every 5-minute cycle) but do notify again if the
    # price dips back below target and later crosses again. Lives only in
    # memory, for as long as this process keeps running — a service restart
    # clears it.
    breakout_state: dict[str, bool] = {}

    while True:
        if not market_is_open():
            await asyncio.sleep(300)
            continue

        targets = get_watchlist()
        prices = get_latest_prices(list(targets.keys()))

        # Collect every new breakout from this cycle, then send them as one
        # combined Telegram message instead of one message per stock.
        new_breakouts: list[tuple[str, float, float]] = []

        for symbol, price in prices.items():
            target = targets.get(symbol)
            if target is None:
                continue

            if breakout_detected(price, target):
                if not breakout_state.get(symbol):
                    new_breakouts.append((symbol, price, target))
                    breakout_state[symbol] = True
            else:
                # Price dipped back below target - reset so the next
                # crossing sends a fresh notification.
                breakout_state[symbol] = False

        await send_telegram_notification(new_breakouts)

        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(strategy_loop())
