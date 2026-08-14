"""
Excel watchlist source.

Reads stock symbols from a watchlist Excel file, then looks up each
symbol's live price on Yahoo Finance (using the `yfinance` package).
"""

from collections.abc import Iterator
from datetime import datetime

import openpyxl
import pandas as pd
import yfinance as yf
from openpyxl.styles import Font

from app.core.logging import get_logger
from app.domain.entities.stock import Stock, StockSourceType

logger = get_logger(__name__)


class ExcelWatchlistSource:
    """Reads stocks from a local Excel watchlist file and fetches their live price."""

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self._sheet_breakout = "Breakout Stocks CMP"
        self._sheet_watch_buy_range = "Buying Range Stocks CMP"

    @property
    def name(self) -> str:
        return "excel_watchlist"

    def iterate_symbol_info(self, worksheet, symbolList: list[str]):
        # Common to every sheet: map header names -> column numbers, fetch each
        # symbol from Yahoo Finance, and write the columns every sheet shares
        # (Company Name, Sector, CMP, Volume, Fetch Data, Update Time).
        # Yields (row, current_price, column_of, stock) so each sheet-specific
        # method can add its own extra columns (BreakOut, Watching Level, ...).
        header_row = 2  # row 1 is the title, row 2 has the real column names

        # Map header name -> column number, e.g. {"Symbol": 2, "CMP (₹)": 5, ...}
        column_of = {}
        for cell in worksheet[header_row]:
            if cell.value:
                column_of[str(cell.value).strip()] = cell.column

        # Map each symbol -> its row number, by scanning the Symbol column.
        symbol_column = column_of["Symbol"]
        row_of_symbol = {}
        for row in range(header_row + 1, worksheet.max_row + 1):
            cell_value = worksheet.cell(row=row, column=symbol_column).value
            if cell_value:
                row_of_symbol[str(cell_value).strip().upper()] = row

        for raw_symbol in symbolList:
            symbol = str(raw_symbol).strip().upper()
            row = row_of_symbol.get(symbol)

            # Yahoo Finance needs the ".NS" suffix for NSE-listed stocks.
            yahoo_symbol = symbol + ".NS"

            try:
                info = yf.Ticker(yahoo_symbol).info
                logger.info(info)
            except Exception as err:
                print(f"Could not fetch {symbol}: {err}")
                if row:
                    worksheet.cell(row=row, column=column_of["Fetch Data"], value="Failed")
                continue

            company_name = info.get("longName") or info.get("shortName") or symbol
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            volume = info.get("volume") or info.get("regularMarketVolume")
            sector = info.get("industry") or info.get("sector")

            if row:
                worksheet.cell(row=row, column=column_of["Company Name"], value=company_name)
                worksheet.cell(row=row, column=column_of["Sector"], value=sector)
                worksheet.cell(row=row, column=column_of["CMP (₹)"], value=current_price)
                worksheet.cell(row=row, column=column_of["Volume"], value=volume)
                worksheet.cell(row=row, column=column_of["Fetch Data"], value="Success")
                worksheet.cell(row=row, column=column_of["Update Time"], value=datetime.now())

            stock = Stock(
                symbol=symbol,
                name=company_name,
                exchange="NSE",
                source=StockSourceType.EXCEL_WATCHLIST,
                cmp=current_price,
            )
            yield row, current_price, column_of, stock

    def iterate_breakout_symbol(self, symbolList: list[str]) -> Iterator[Stock]:
        # Open the real workbook (not through pandas) so we can edit specific
        # cells and save it back without touching the other sheets/formatting.
        workbook = openpyxl.load_workbook(self._file_path)
        worksheet = workbook[self._sheet_breakout]
        green_bold = Font(color="008000", bold=True)

        for row, current_price, column_of, stock in self.iterate_symbol_info(
            worksheet, symbolList
        ):
            if row:
                # BreakOut: did the price reach/cross the Target price for this row?
                target = worksheet.cell(row=row, column=column_of["Target"]).value
                crossed = False
                if target is not None and current_price is not None and current_price >= target:
                    crossed = True

                breakout_cell = worksheet.cell(row=row, column=column_of["BreakOut"])
                if crossed:
                    breakout_cell.value = "Done"
                    breakout_cell.font = green_bold
                else:
                    breakout_cell.value = "NA"
                    breakout_cell.font = Font()

            yield stock

        # Save all the cell updates back to the file, once, after every symbol is done.
        workbook.save(self._file_path)

    def iterate_symbol_buying_range(self, symbolList: list[str]) -> Iterator[Stock]:
        # Same idea as iterate_breakout_symbol(), but for the "Buying Range Stocks CMP"
        # sheet, which has different columns (Watching Target / Watching Level(1-2%)
        # instead of Target / BreakOut).
        workbook = openpyxl.load_workbook(self._file_path)
        worksheet = workbook[self._sheet_watch_buy_range]
        green_bold = Font(color="008000", bold=True)
        red_bold = Font(color="FF0000", bold=True)

        for row, current_price, column_of, stock in self.iterate_symbol_info(
            worksheet, symbolList
        ):
            if row:
                # Watching Level: has CMP come within 2% of the Watching Target (either side)?
                watching_target = worksheet.cell(
                    row=row, column=column_of["Watching Target"]
                ).value
                has_both_values = watching_target is not None and current_price is not None
                reached = False
                if has_both_values and watching_target != 0:
                    percent_gap = abs(current_price - watching_target) / watching_target * 100
                    if percent_gap <= 2:
                        reached = True

                watching_level_cell = worksheet.cell(
                    row=row, column=column_of["Watching Level(1-2%)"]
                )
                if reached:
                    watching_level_cell.value = "Reached"
                    watching_level_cell.font = green_bold
                else:
                    watching_level_cell.value = "Not Reached"
                    watching_level_cell.font = red_bold

            yield stock

        # Save all the cell updates back to the file, once, after every symbol is done.
        workbook.save(self._file_path)

    async def fetch_stocks(self) -> list[Stock]:
        # --- Breakout Stocks CMP sheet ---
        # header=1 because row 0 in this sheet is just a title ("STOCKS - CMP Dashboard"),
        # the real column names (Symbol, Company Name, ...) start on row 1.
        df_breakout = pd.read_excel(self._file_path, sheet_name=self._sheet_breakout, header=1)
        breakout_symbols = df_breakout["Symbol"].dropna().tolist()
        print("Breakout sheet stocks :", breakout_symbols)
        breakout_stocks = [stock for stock in self.iterate_breakout_symbol(breakout_symbols)]

        # --- Buying Range Stocks CMP sheet ---
        df_buy_range = pd.read_excel(
            self._file_path, sheet_name=self._sheet_watch_buy_range, header=1
        )
        buy_range_symbols = df_buy_range["Symbol"].dropna().tolist()
        print("Buying Range sheet stocks :", buy_range_symbols)
        buy_range_stocks = [stock for stock in self.iterate_symbol_buying_range(buy_range_symbols)]

        # Step 3: combine both sheets' stocks into a single result for this run.
        return breakout_stocks + buy_range_stocks
