"""
Shared Yahoo Finance lookup.

One function, used by both `excel_source.py` (fetching a batch of stocks
for the API) and the standalone `stock_monitor.py` script (checking prices
every 5 minutes) — so both places handle the ".NS" suffix and fetch errors
the same way instead of duplicating this logic.
"""

import yfinance as yf


def fetch_cmp(symbol: str) -> dict | None:
    """Fetch Yahoo Finance's live quote info for one NSE symbol, or None on failure."""
    yahoo_symbol = symbol if "." in symbol else f"{symbol}.NS"
    try:
        return yf.Ticker(yahoo_symbol).info
    except Exception as err:
        print(f"Could not fetch {symbol}: {err}")
        return None
