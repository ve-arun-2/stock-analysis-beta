"""
Excel watchlist source.

Reads stock symbols from a watchlist Excel workbook stored in S3, then looks
up each symbol's live price on Yahoo Finance (using the `yfinance` package).
The workbook is fetched from and saved back to S3 — never to local disk.
"""

from collections.abc import Iterator
from io import BytesIO

import openpyxl
import pandas as pd

from app.core.logging import get_logger
from app.domain.entities.stock import Stock
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
from app.infrastructure.repositories.stock_alert_repository import StockAlertRepository

logger = get_logger(__name__)

class ExcelWatchlistSource:
    """Reads stocks from the S3-hosted Excel watchlist and fetches their live price."""

    def __init__(self, stock_alert_repo: StockAlertRepository) -> None:
        self._sheet_breakout = "Breakout Stocks CMP"
        self._sheet_watch_buy_range = "Buying Range Stocks CMP"
        self._stock_alert_repo = stock_alert_repo

    @property
    def name(self) -> str:
        return "excel_watchlist"

    def iterate_symbol_info(self, worksheet, symbolList: list[str]):
        # Common to every sheet: map header names -> column numbers, fetch each
        # symbol from Yahoo Finance, and write the columns every sheet shares
        # (Company Name, Sector, CMP, Volume, Fetch Data, Update Time).
        # Yields (row, current_price, column_of, stock) so each sheet-specific
        # method can add its own extra columns (BreakOut, Watching Level, ...).
        column_of = build_column_map(worksheet)
        symbol_column = column_of["Symbol"]
        row_of_symbol = build_row_map(worksheet, symbol_column)

        for raw_symbol in symbolList:
            symbol = str(raw_symbol).strip().upper()
            row = row_of_symbol.get(symbol)

            info = fetch_cmp_yfinance(symbol)
            if info is None:
                if row:
                    worksheet.cell(row=row, column=column_of["Fetch Data"], value="Failed")
                continue
            # logger.info(info)

            breakout_price = (
                worksheet.cell(row=row, column=column_of["Target"]).value
                if worksheet.title == self._sheet_breakout
                else None
            )
            company_name = info.get("longName") or info.get("shortName") or symbol
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            volume = info.get("volume") or info.get("regularMarketVolume")
            sector = info.get("industry") or info.get("sector")
            market_cap = info.get("marketCap")
            average_daily_10days_volume = info.get("averageVolume10days")
            exchange = info.get("fullExchangeName") or "NSE"

            if row:
                write_common_fields(
                    worksheet, row, column_of, current_price, volume, sector, company_name
                )

            stock = Stock(
                symbol=symbol,
                volume=volume,
                average_daily_10days_volume=average_daily_10days_volume,
                company_name=company_name,
                exchange=exchange,
                sector=sector,
                market_cap=market_cap,
                breakout_price=breakout_price,
            )
            print(stock)
            yield row, current_price, column_of, stock

    async def iterate_breakout_symbol(self, symbolList: list[str]) -> Iterator[Stock]:
        # Open the real workbook (not through pandas) so we can edit specific
        # cells and save it back without touching the other sheets/formatting.
        workbook = openpyxl.load_workbook(download_watchlist())
        worksheet = workbook[self._sheet_breakout]

        for row, current_price, column_of, stock in self.iterate_symbol_info(worksheet, symbolList):
            if row:
                target = worksheet.cell(row=row, column=column_of["Target"]).value
                is_break_out_crossed = write_breakout_status(worksheet, row, column_of, current_price, target)
                if(is_break_out_crossed):
                    await self._stock_alert_repo.add(stock) # Call Alert Repo

            yield stock

        # Save all the cell updates, once, after every symbol is done, and
        # upload the updated workbook back to the same S3 key.
        buffer = BytesIO()
        workbook.save(buffer)
        upload_watchlist(buffer)

    def iterate_symbol_buying_range(self, symbolList: list[str]) -> Iterator[Stock]:
        # Same idea as iterate_breakout_symbol(), but for the "Buying Range Stocks CMP"
        # sheet, which has different columns (Watching Target / Watching Level(1-2%)
        # instead of Target / BreakOut).
        workbook = openpyxl.load_workbook(download_watchlist())
        worksheet = workbook[self._sheet_watch_buy_range]

        for row, current_price, column_of, stock in self.iterate_symbol_info(worksheet, symbolList):
            if row:
                watching_target = worksheet.cell(row=row, column=column_of["Watching Target"]).value
                write_watching_level_status(
                    worksheet, row, column_of, current_price, watching_target
                )

            yield stock

        # Save all the cell updates, once, after every symbol is done, and
        # upload the updated workbook back to the same S3 key.
        buffer = BytesIO()
        workbook.save(buffer)
        upload_watchlist(buffer)

    async def fetch_stocks(self) -> list[Stock]:
        # --- Breakout Stocks CMP sheet ---
        # header=1 because row 0 in this sheet is just a title ("STOCKS - CMP Dashboard"),
        # the real column names (Symbol, Company Name, ...) start on row 1.
        df_breakout = pd.read_excel(download_watchlist(), sheet_name=self._sheet_breakout, header=1)
        breakout_symbols = df_breakout["Symbol"].dropna().tolist()
        
        print("Breakout sheet stocks :", breakout_symbols)
        breakout_stocks = [stock async for stock in self.iterate_breakout_symbol(breakout_symbols)]

        # --- Buying Range Stocks CMP sheet ---
        df_buy_range = pd.read_excel(
            download_watchlist(), sheet_name=self._sheet_watch_buy_range, header=1
        )
        buy_range_symbols = df_buy_range["Symbol"].dropna().tolist()
        print("Buying Range sheet stocks :", buy_range_symbols)
        buy_range_stocks = [stock for stock in self.iterate_symbol_buying_range(buy_range_symbols)]

        # Step 3: combine both sheets' stocks into a single result for this run.
        return breakout_stocks + buy_range_stocks
