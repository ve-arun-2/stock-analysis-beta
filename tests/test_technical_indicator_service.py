"""Tests for `TechnicalIndicatorService` — repos are hand-rolled fakes."""

from datetime import date, timedelta

from app.services.technical_indicator_service import TechnicalIndicatorService


class _FakeDailyRepo:
    def __init__(self, grouped: dict[str, list[dict]]) -> None:
        self._grouped = grouped
        self.asof: date | None = None

    async def list_bars_asof(self, trading_date: date):
        self.asof = trading_date
        return self._grouped


class _FakeSnapshotRepo:
    def __init__(self) -> None:
        self.rows: list[dict] | None = None

    async def upsert_snapshots(self, rows: list[dict]) -> int:
        self.rows = rows
        return len(rows)


def _bars(count: int) -> list[dict]:
    return [
        {
            "trading_date": date(2025, 1, 1) + timedelta(days=i),
            "open": 100.0 + i,
            "high": 101.0 + i,
            "low": 99.0 + i,
            "close": 100.0 + i,
            "volume": 1_000 + i,
        }
        for i in range(count)
    ]


async def test_generate_upserts_one_snapshot_per_symbol_and_returns_them():
    daily = _FakeDailyRepo({"RELIANCE": _bars(25), "TCS": _bars(25)})
    snapshots = _FakeSnapshotRepo()
    service = TechnicalIndicatorService(daily, snapshots)

    result = await service.generate(trading_date=date(2025, 1, 25))

    assert daily.asof == date(2025, 1, 25)
    assert {row["symbol"] for row in result} == {"RELIANCE", "TCS"}
    assert snapshots.rows == result
    reliance = next(row for row in result if row["symbol"] == "RELIANCE")
    assert reliance["trading_date"] == date(2025, 1, 25)
    assert reliance["sma_20"] is not None
    assert reliance["sma_200"] is None  # not enough history


async def test_generate_defaults_trading_date_to_today_ist():
    daily = _FakeDailyRepo({})
    service = TechnicalIndicatorService(daily, _FakeSnapshotRepo())

    await service.generate()

    assert daily.asof is not None  # a concrete date was resolved


async def test_generate_skips_symbols_with_no_bars():
    daily = _FakeDailyRepo({"RELIANCE": _bars(10), "EMPTY": []})
    snapshots = _FakeSnapshotRepo()
    service = TechnicalIndicatorService(daily, snapshots)

    result = await service.generate(trading_date=date(2025, 1, 10))

    assert [row["symbol"] for row in result] == ["RELIANCE"]


async def test_generate_with_nothing_for_that_day():
    daily = _FakeDailyRepo({})
    snapshots = _FakeSnapshotRepo()
    service = TechnicalIndicatorService(daily, snapshots)

    assert await service.generate(trading_date=date(2025, 1, 1)) == []
    assert snapshots.rows == []
