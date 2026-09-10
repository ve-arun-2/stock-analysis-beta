"""
Technical indicators.

Small, self-contained functions — one per indicator — plus a `build_snapshot`
assembler that maps a symbol's daily bars to every column of
`StockTechnicalSnapshotModel`.

Each indicator function takes plain sequences of floats (so it is easy to expose
as an agent tool later), computes with pandas, and returns a rounded ``float``,
a small ``dict`` for multi-value indicators, or ``None`` when there is not enough
history for the requested period.
"""

from collections.abc import Sequence

import pandas as pd

Number = float | int


def _series(values: Sequence[Number | None]) -> pd.Series:
    """Coerce to a float Series, dropping missing values."""
    return pd.Series(values, dtype="float64").dropna().reset_index(drop=True)


def _round(value: object, ndigits: int = 2) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), ndigits)


def _ratio(current: Number | None, average: float | None) -> float | None:
    if current is None or not average:
        return None
    return round(float(current) / average, 2)


def _above(price: float | None, level: float | None) -> bool | None:
    if price is None or level is None:
        return None
    return bool(price > level)


# --------------------------------------------------------------------------
# Moving averages
# --------------------------------------------------------------------------


def sma(values: Sequence[Number | None], period: int) -> float | None:
    """Simple moving average of the last `period` values."""
    series = _series(values)
    if len(series) < period:
        return None
    return _round(series.rolling(period).mean().iloc[-1])


def ema(values: Sequence[Number | None], period: int) -> float | None:
    """Exponential moving average (span = `period`)."""
    series = _series(values)
    if len(series) < period:
        return None
    return _round(series.ewm(span=period, adjust=False).mean().iloc[-1])


# --------------------------------------------------------------------------
# Momentum
# --------------------------------------------------------------------------


def rsi(closes: Sequence[Number | None], period: int = 14) -> float | None:
    """Wilder's Relative Strength Index."""
    series = _series(closes)
    if len(series) < period + 1:
        return None

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return _round(100 - 100 / (1 + rs))


def macd(
    closes: Sequence[Number | None],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, float | None]:
    """MACD line, signal line and histogram."""
    series = _series(closes)
    if len(series) < slow + signal:
        return {"macd": None, "signal": None, "histogram": None}

    macd_line = (
        series.ewm(span=fast, adjust=False).mean() - series.ewm(span=slow, adjust=False).mean()
    )
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd": _round(macd_line.iloc[-1]),
        "signal": _round(signal_line.iloc[-1]),
        "histogram": _round(histogram.iloc[-1]),
    }


def stochastic(
    highs: Sequence[Number | None],
    lows: Sequence[Number | None],
    closes: Sequence[Number | None],
    k_period: int = 14,
    d_period: int = 3,
) -> dict[str, float | None]:
    """Stochastic oscillator %K and %D."""
    high, low, close = _series(highs), _series(lows), _series(closes)
    if min(len(high), len(low), len(close)) < k_period + d_period:
        return {"k": None, "d": None}

    lowest = low.rolling(k_period).min()
    highest = high.rolling(k_period).max()
    percent_k = 100 * (close - lowest) / (highest - lowest)
    percent_d = percent_k.rolling(d_period).mean()
    return {"k": _round(percent_k.iloc[-1]), "d": _round(percent_d.iloc[-1])}


# --------------------------------------------------------------------------
# Volatility / trend
# --------------------------------------------------------------------------


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)


def atr(
    highs: Sequence[Number | None],
    lows: Sequence[Number | None],
    closes: Sequence[Number | None],
    period: int = 14,
) -> float | None:
    """Wilder's Average True Range."""
    high, low, close = _series(highs), _series(lows), _series(closes)
    if min(len(high), len(low), len(close)) < period + 1:
        return None
    true_range = _true_range(high, low, close)
    return _round(true_range.ewm(alpha=1 / period, adjust=False).mean().iloc[-1])


def adx(
    highs: Sequence[Number | None],
    lows: Sequence[Number | None],
    closes: Sequence[Number | None],
    period: int = 14,
) -> float | None:
    """Average Directional Index (Wilder)."""
    high, low, close = _series(highs), _series(lows), _series(closes)
    if min(len(high), len(low), len(close)) < 2 * period:
        return None

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = ((up_move > down_move) & (up_move > 0)) * up_move
    minus_dm = ((down_move > up_move) & (down_move > 0)) * down_move

    atr_series = _true_range(high, low, close).ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_series
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_series

    directional = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA)
    return _round((100 * directional).ewm(alpha=1 / period, adjust=False).mean().iloc[-1])


def bollinger(
    closes: Sequence[Number | None],
    period: int = 20,
    num_std: float = 2.0,
) -> dict[str, float | None]:
    """Bollinger Bands (SMA +/- num_std * population stddev)."""
    series = _series(closes)
    if len(series) < period:
        return {"upper": None, "middle": None, "lower": None}
    middle = series.rolling(period).mean().iloc[-1]
    deviation = series.rolling(period).std(ddof=0).iloc[-1]
    return {
        "upper": _round(middle + num_std * deviation),
        "middle": _round(middle),
        "lower": _round(middle - num_std * deviation),
    }


# --------------------------------------------------------------------------
# Price / volume helpers
# --------------------------------------------------------------------------


def pct_change(values: Sequence[Number | None], periods: int) -> float | None:
    """Percent change over the last `periods` bars."""
    series = _series(values)
    if len(series) < periods + 1:
        return None
    previous = series.iloc[-1 - periods]
    if previous == 0:
        return None
    return _round((series.iloc[-1] - previous) / previous * 100)


def rolling_high(values: Sequence[Number | None], window: int) -> float | None:
    """Highest value over the last `window` bars (or all bars if fewer)."""
    series = _series(values)
    if series.empty:
        return None
    return _round(series.tail(window).max())


def rolling_low(values: Sequence[Number | None], window: int) -> float | None:
    """Lowest value over the last `window` bars (or all bars if fewer)."""
    series = _series(values)
    if series.empty:
        return None
    return _round(series.tail(window).min())


def distance_pct(price: float | None, reference: float | None) -> float | None:
    """How far `price` sits above/below `reference`, in percent."""
    if price is None or not reference:
        return None
    return _round((price - reference) / reference * 100)


# --------------------------------------------------------------------------
# Trend state
# --------------------------------------------------------------------------


def is_golden_cross(
    closes: Sequence[Number | None], short: int = 50, long: int = 200
) -> bool | None:
    """SMA(short) crossed above SMA(long) on the latest bar."""
    series = _series(closes)
    if len(series) < long + 1:
        return None
    short_ma = series.rolling(short).mean()
    long_ma = series.rolling(long).mean()
    return bool(short_ma.iloc[-2] <= long_ma.iloc[-2] and short_ma.iloc[-1] > long_ma.iloc[-1])


def is_death_cross(
    closes: Sequence[Number | None], short: int = 50, long: int = 200
) -> bool | None:
    """SMA(short) crossed below SMA(long) on the latest bar."""
    series = _series(closes)
    if len(series) < long + 1:
        return None
    short_ma = series.rolling(short).mean()
    long_ma = series.rolling(long).mean()
    return bool(short_ma.iloc[-2] >= long_ma.iloc[-2] and short_ma.iloc[-1] < long_ma.iloc[-1])


def classify_trend(
    close: float | None, ema_50: float | None, ema_200: float | None
) -> str | None:
    """A coarse trend label from price vs the 50/200 EMAs."""
    if close is None or ema_50 is None or ema_200 is None:
        return None
    if close > ema_50 > ema_200:
        return "strong_uptrend"
    if close > ema_200:
        return "uptrend"
    if close < ema_50 < ema_200:
        return "strong_downtrend"
    if close < ema_200:
        return "downtrend"
    return "sideways"


# --------------------------------------------------------------------------
# Assembler
# --------------------------------------------------------------------------


def build_snapshot(bars: list[dict]) -> dict:
    """Map a symbol's daily bars (oldest -> newest) to snapshot columns.

    `bars` items must have: trading_date, open, high, low, close, volume.
    Returns a dict keyed by every `StockTechnicalSnapshotModel` column except
    `id`, `symbol` and `calculated_at`. Anything that needs more history than is
    available comes back as `None`.
    """
    if not bars:
        return {}

    highs = [bar["high"] for bar in bars]
    lows = [bar["low"] for bar in bars]
    closes = [bar["close"] for bar in bars]
    volumes = [bar["volume"] for bar in bars]
    last = bars[-1]
    close = last["close"]
    last_volume = last["volume"]

    ema_20 = ema(closes, 20)
    ema_50 = ema(closes, 50)
    ema_200 = ema(closes, 200)
    macd_values = macd(closes)
    bands = bollinger(closes)
    stoch = stochastic(highs, lows, closes)
    atr_14 = atr(highs, lows, closes, 14)

    fifty_two_week_high = rolling_high(highs, 252)
    fifty_two_week_low = rolling_low(lows, 252)

    avg_vol_5 = sma(volumes, 5)
    avg_vol_10 = sma(volumes, 10)
    avg_vol_20 = sma(volumes, 20)
    avg_vol_50 = sma(volumes, 50)

    return {
        "trading_date": last["trading_date"],
        "close": _round(close),
        "day_high": _round(last["high"]),
        "day_low": _round(last["low"]),
        "fifty_two_week_high": fifty_two_week_high,
        "fifty_two_week_low": fifty_two_week_low,
        "all_time_high": rolling_high(highs, len(highs)),
        "all_time_low": rolling_low(lows, len(lows)),
        "distance_from_52w_high_pct": distance_pct(close, fifty_two_week_high),
        "distance_from_52w_low_pct": distance_pct(close, fifty_two_week_low),
        "sma_20": sma(closes, 20),
        "sma_50": sma(closes, 50),
        "sma_100": sma(closes, 100),
        "sma_200": sma(closes, 200),
        "ema_9": ema(closes, 9),
        "ema_20": ema_20,
        "ema_50": ema_50,
        "ema_100": ema(closes, 100),
        "ema_200": ema_200,
        "distance_from_ema_20_pct": distance_pct(close, ema_20),
        "distance_from_ema_50_pct": distance_pct(close, ema_50),
        "distance_from_ema_200_pct": distance_pct(close, ema_200),
        "change_1d_pct": pct_change(closes, 1),
        "change_5d_pct": pct_change(closes, 5),
        "change_10d_pct": pct_change(closes, 10),
        "change_20d_pct": pct_change(closes, 20),
        "change_50d_pct": pct_change(closes, 50),
        "change_200d_pct": pct_change(closes, 200),
        "volume": _round(last_volume),
        "average_volume_5d": avg_vol_5,
        "average_volume_10d": avg_vol_10,
        "average_volume_20d": avg_vol_20,
        "average_volume_50d": avg_vol_50,
        "volume_ratio_5d": _ratio(last_volume, avg_vol_5),
        "volume_ratio_10d": _ratio(last_volume, avg_vol_10),
        "volume_ratio_20d": _ratio(last_volume, avg_vol_20),
        "volume_ratio_50d": _ratio(last_volume, avg_vol_50),
        "rsi_14": rsi(closes, 14),
        "macd": macd_values["macd"],
        "macd_signal": macd_values["signal"],
        "macd_histogram": macd_values["histogram"],
        "atr_14": atr_14,
        "atr_14_pct": _round(atr_14 / close * 100) if atr_14 is not None and close else None,
        "adx_14": adx(highs, lows, closes, 14),
        "bollinger_upper": bands["upper"],
        "bollinger_middle": bands["middle"],
        "bollinger_lower": bands["lower"],
        "stochastic_k": stoch["k"],
        "stochastic_d": stoch["d"],
        "price_above_ema_50": _above(close, ema_50),
        "price_above_ema_200": _above(close, ema_200),
        "golden_cross": is_golden_cross(closes),
        "death_cross": is_death_cross(closes),
        "trend": classify_trend(close, ema_50, ema_200),
    }
