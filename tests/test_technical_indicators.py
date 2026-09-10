"""Unit tests for the pure indicator functions + `build_snapshot`."""

from datetime import date, timedelta

from app.domain.entities import technical_indicators as ti
from app.infrastructure.database.models.stock_technical_snapshot_model import (
    StockTechnicalSnapshotModel,
)


def test_sma_and_none_when_too_short():
    assert ti.sma([1, 2, 3, 4, 5], 3) == 4.0
    assert ti.sma([1, 2], 5) is None


def test_sma_ignores_missing_values():
    # Nones dropped -> [1, 3, 5] -> mean
    assert ti.sma([1, None, 3, None, 5], 3) == 3.0


def test_ema_matches_hand_calculation():
    # span=3 -> alpha 0.5, adjust=False, seeded at first value
    assert ti.ema([1, 2, 3, 4, 5], 3) == 4.06


def test_rsi_is_100_when_only_gains():
    assert ti.rsi(list(range(1, 40))) == 100.0


def test_rsi_none_when_too_short():
    assert ti.rsi([1, 2, 3], 14) is None


def test_macd_none_dict_when_too_short():
    assert ti.macd([1.0] * 10) == {"macd": None, "signal": None, "histogram": None}


def test_bollinger_collapses_to_price_on_flat_series():
    assert ti.bollinger([10.0] * 20) == {"upper": 10.0, "middle": 10.0, "lower": 10.0}


def test_pct_change():
    assert ti.pct_change([100, 110], 1) == 10.0
    assert ti.pct_change([100, 105, 120], 2) == 20.0
    assert ti.pct_change([100], 5) is None


def test_rolling_high_low():
    assert ti.rolling_high([1, 5, 3, 2], 2) == 3.0
    assert ti.rolling_high([1, 5, 3], 10) == 5.0
    assert ti.rolling_low([4, 1, 3], 10) == 1.0
    assert ti.rolling_high([], 10) is None


def test_distance_pct():
    assert ti.distance_pct(110, 100) == 10.0
    assert ti.distance_pct(90, 100) == -10.0
    assert ti.distance_pct(100, None) is None
    assert ti.distance_pct(100, 0) is None


def test_crosses_need_full_history():
    assert ti.is_golden_cross([1.0] * 50) is None
    assert ti.is_death_cross([1.0] * 50) is None


def test_classify_trend():
    assert ti.classify_trend(120, 110, 100) == "strong_uptrend"
    assert ti.classify_trend(105, 110, 100) == "uptrend"
    assert ti.classify_trend(80, 90, 100) == "strong_downtrend"
    assert ti.classify_trend(None, 1, 2) is None


def _rising_bars(count: int) -> list[dict]:
    bars = []
    price = 100.0
    for i in range(count):
        price *= 1.01
        bars.append(
            {
                "trading_date": date(2025, 1, 1) + timedelta(days=i),
                "open": round(price * 0.999, 2),
                "high": round(price * 1.01, 2),
                "low": round(price * 0.99, 2),
                "close": round(price, 2),
                "volume": 100_000 + i,
            }
        )
    return bars


def test_build_snapshot_covers_exactly_the_model_columns():
    snapshot = ti.build_snapshot(_rising_bars(30))

    model_columns = {
        column.name for column in StockTechnicalSnapshotModel.__table__.columns
    } - {"id", "symbol", "calculated_at"}

    assert set(snapshot) == model_columns


def test_build_snapshot_short_history_nulls_long_periods_but_fills_short_ones():
    snapshot = ti.build_snapshot(_rising_bars(25))

    assert snapshot["sma_20"] is not None
    assert snapshot["sma_200"] is None
    assert snapshot["ema_200"] is None
    assert snapshot["change_1d_pct"] is not None
    assert snapshot["change_200d_pct"] is None
    assert snapshot["trading_date"] == date(2025, 1, 25)


def test_build_snapshot_empty_bars():
    assert ti.build_snapshot([]) == {}
