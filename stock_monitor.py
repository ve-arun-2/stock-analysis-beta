"""
Stock monitor.

Runs continuously as a systemd service (see stock_monitor.service — started
once, kept alive with `Restart=always`). While the NSE market is open, it
checks every watched stock's live price every 5 minutes — both the Breakout
sheet (Target crossings) and the Buying Range sheet (Watching Target
proximity) — writes the results back to the S3 workbook, and can send a
Telegram message the first time a stock crosses.

This is a standalone script, separate from the FastAPI app, but it reuses
the app's settings and the same shared S3/sheet helpers that excel_source.py
uses (watchlist_client_common), so the column-mapping and cell-writing logic
isn't duplicated between the two.
"""

import asyncio
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

import httpx
import openpyxl

from app.core.config import settings
from app.infrastructure.database.session import AsyncSessionFactory
from app.infrastructure.repositories.stock_alert_repository import StockAlertRepository
from app.infrastructure.sources.watchlist_client_common import (
    build_column_map,
    build_row_map,
    download_watchlist,
    upload_watchlist,
    write_breakout_status,
    write_common_fields,
    write_watching_level_status,
)
from app.infrastructure.sources.yfinance_client import fetch_cmp_yfinance
from app.domain.entities.stock import Stock

BREAKOUT_SHEET = "Breakout Stocks CMP"
BUYING_RANGE_SHEET = "Buying Range Stocks CMP"

IST = ZoneInfo("Asia/Kolkata")

def market_is_open() -> bool:
    """NSE regular trading hours: Monday-Friday, 9:15-15:30 IST."""
    # now = datetime.now(IST)

    # if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
    #     return False

    # market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    # market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    # return market_open <= now <= market_close
    return True  # hardcoded on for testing


def _fetch_and_write_common_fields(worksheet, row: int, column_of: dict[str, int], symbol: str):
    """Fetch one symbol from Yahoo Finance and write the columns every sheet shares.

    Returns (price, info) — info is the raw Yahoo Finance quote dict, needed by
    callers that build a `Stock` for the alert repository. Returns (None, None)
    if the fetch failed (Fetch Data is marked "Failed" on the row in that case).
    """
    info = fetch_cmp_yfinance(symbol)
    if info is None:
        worksheet.cell(row=row, column=column_of["Fetch Data"], value="Failed")
        return None, None

    company_name = info.get("longName") or info.get("shortName") or symbol
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    volume = info.get("volume") or info.get("regularMarketVolume")
    sector = info.get("industry") or info.get("sector")

    write_common_fields(worksheet, row, column_of, price, volume, sector, company_name)
    return price, info


async def process_breakout_sheet(
    breakout_state: dict[str, bool], 
    stock_alert_repo: StockAlertRepository
) -> list[tuple[str, float, float]]:
    """Check every symbol in the Breakout sheet, write results, return newly-crossed stocks."""
    workbook = openpyxl.load_workbook(download_watchlist())
    worksheet = workbook[BREAKOUT_SHEET]

    column_of = build_column_map(worksheet)
    row_of_symbol = build_row_map(worksheet, column_of["Symbol"])

    new_breakouts: list[tuple[str, float, float]] = []

    for symbol, row in row_of_symbol.items():
        price, info = _fetch_and_write_common_fields(worksheet, row, column_of, symbol)
        if price is None:
            continue

        target = worksheet.cell(row=row, column=column_of["Target"]).value
        crossed = write_breakout_status(worksheet, row, column_of, price, target)

        if crossed and target is not None:
            if not breakout_state.get(symbol):
                new_breakouts.append((symbol, price, target))
                breakout_state[symbol] = True

            stock = Stock(
                symbol=symbol,
                company_name=info.get("longName") or info.get("shortName") or symbol,
                exchange=info.get("fullExchangeName") or "NSE",
                sector=info.get("industry") or info.get("sector"),
                market_cap=info.get("marketCap"),
                volume=info.get("volume") or info.get("regularMarketVolume"),
                average_daily_10days_volume=info.get("averageVolume10days"),
                breakout_price=target,
            )
            await stock_alert_repo.add(stock)  # Call Alert Repo
        else:
            # Price dipped back below target - reset so the next crossing
            # sends a fresh notification.
            breakout_state[symbol] = False

    buffer = BytesIO()
    workbook.save(buffer)
    upload_watchlist(buffer)
    return new_breakouts


def process_buying_range_sheet(watch_state: dict[str, bool]) -> list[tuple[str, float, float]]:
    """Check every symbol in the Buying Range sheet, write results, return newly-reached stocks."""
    workbook = openpyxl.load_workbook(download_watchlist())
    worksheet = workbook[BUYING_RANGE_SHEET]

    column_of = build_column_map(worksheet)
    row_of_symbol = build_row_map(worksheet, column_of["Symbol"])

    newly_reached: list[tuple[str, float, float]] = []

    for symbol, row in row_of_symbol.items():
        price, _info = _fetch_and_write_common_fields(worksheet, row, column_of, symbol)
        if price is None:
            continue

        watching_target = worksheet.cell(row=row, column=column_of["Watching Target"]).value
        reached = write_watching_level_status(worksheet, row, column_of, price, watching_target)

        if reached and watching_target is not None:
            if not watch_state.get(symbol):
                newly_reached.append((symbol, price, watching_target))
                watch_state[symbol] = True
        else:
            # Price moved back out of range - reset so the next time it
            # comes within range sends a fresh notification.
            watch_state[symbol] = False

    buffer = BytesIO()
    workbook.save(buffer)
    upload_watchlist(buffer)
    return newly_reached


async def send_telegram_notification(label: str, breakouts: list[tuple[str, float, float]]) -> None:
    """Send one Telegram message listing every stock that changed status this cycle."""
    if not breakouts:
        return

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        symbols = [symbol for symbol, _, _ in breakouts]
        print(f"Telegram not configured — skipping {label} alert for {symbols}")
        return

    label_msg = ""
    if(label == "BREAKOUT_PRICE"):
        label_msg = "<symbol> — 🚀Crossed Breakout Price-> <target> !! CMP: <price>"
    elif(label == "BUY_RANGE_PRICE"):
        label_msg = "<symbol> — 🚨Entered the buying range-> <target> !! CMP: <price>"

    lines = []
    for symbol, price, target in breakouts:
        line = label_msg.replace("<symbol>", str(symbol))
        line = line.replace("<target>", str(target))
        line = line.replace("<price>", str(price))
        lines.append(line)
    message = "\n".join(lines)
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"

    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, data={"chat_id": settings.telegram_chat_id, "text": message})
        except Exception as err:
            print(f"Could not send Telegram notification: {err}")


async def strategy_loop() -> None:
    # Remembers which symbols are currently above target / within watching
    # range, so we notify once per crossing (not every cycle) but do notify
    # again if it drops out and later re-crosses. Lives only in memory, for
    # as long as this process keeps running — a service restart clears it.
    breakout_state: dict[str, bool] = {}
    watch_state: dict[str, bool] = {}

    while True:
        print(f"Check: {datetime.now()}")
        if not market_is_open():
            await asyncio.sleep(300)
            continue

        async with AsyncSessionFactory() as session:
            stock_alert_repo = StockAlertRepository(session)
            new_breakouts = await process_breakout_sheet(breakout_state, stock_alert_repo)

        newly_reached = process_buying_range_sheet(watch_state)

        if new_breakouts or newly_reached:
            print(
                f"New breakouts: {[s for s, _, _ in new_breakouts]}, "
                f"newly in range: {[s for s, _, _ in newly_reached]}"
            )

        await send_telegram_notification("BREAKOUT_PRICE", new_breakouts)
        await send_telegram_notification("BUY_RANGE_PRICE", newly_reached)

        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(strategy_loop())
