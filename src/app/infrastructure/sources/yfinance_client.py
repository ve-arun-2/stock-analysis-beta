"""
Shared Yahoo Finance lookups.

Used by `excel_source.py`, `chartink_source.py` and the standalone
`stock_monitor.py` script — so the ".NS" suffix handling and fetch-error
behaviour live in one place instead of being duplicated.
"""

from datetime import date

import yfinance as yf


def _to_yahoo_symbol(symbol: str) -> str:
    """NSE symbol -> Yahoo ticker ("RELIANCE" -> "RELIANCE.NS")."""
    return symbol if "." in symbol else f"{symbol}.NS"


def _to_float(value: object) -> float | None:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return result if result == result else None  # drop NaN


def fetch_cmp_yfinance(symbol: str) -> dict | None:
    """Fetch Yahoo Finance's live quote info for one NSE symbol, or None on failure."""
    try:
        return yf.Ticker(_to_yahoo_symbol(symbol)).info
    except Exception as err:
        print(f"Could not fetch {symbol}: {err}")
        return None


def fetch_daily_bar_yfinance(symbol: str) -> dict | None:
    """Fetch the most recent daily OHLCV bar for one NSE symbol.

    Returns a dict keyed by the `stock_daily_data` column names
    (`trading_date`, `open`, `high`, `low`, `close`, `volume`, `dividends`,
    `stock_splits`), or None if nothing came back.
    """
    try:
        # auto_adjust=True: `Close` is the (split/dividend-adjusted) close and is
        # reliably populated. With auto_adjust=False yfinance often returns NaN in
        # `Close` for the latest .NS bar (the value only lands in `Adj Close`).
        history = yf.Ticker(_to_yahoo_symbol(symbol)).history(
            period="5d",
            auto_adjust=True,
        )
    except Exception as err:
        print(f"Could not fetch daily bar for {symbol}: {err}")
        return None

    if history is None or history.empty:
        return None

    # Drop a still-forming row for the current session that has no close yet.
    history = history.dropna(subset=["Close"])
    if history.empty:
        return None

    row = history.iloc[-1]
    trading_date = history.index[-1].date()
    if not isinstance(trading_date, date):
        return None

    return {
        "trading_date": trading_date,
        "open": _to_float(row.get("Open")),
        "high": _to_float(row.get("High")),
        "low": _to_float(row.get("Low")),
        "close": _to_float(row.get("Close")),
        "volume": _to_float(row.get("Volume")),
        "dividends": _to_float(row.get("Dividends")),
        "stock_splits": _to_float(row.get("Stock Splits")),
    }
