"""Tests for the shared `ingest_daily_bars` pipeline."""

from datetime import date

import pytest

import app.infrastructure.sources.daily_data_ingest as ingest_mod
from app.infrastructure.sources.daily_data_ingest import IngestEntry, ingest_daily_bars

_BAR = {
    "trading_date": date(2026, 9, 8),
    "open": 10.0,
    "high": 11.0,
    "low": 9.5,
    "close": 10.5,
    "volume": 1000.0,
    "dividends": 0.0,
    "stock_splits": 0.0,
}


class _FakeRepo:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    async def upsert_daily_bars(self, rows: list[dict]) -> int:
        self.rows.extend(rows)
        return len(rows)


async def test_symbols_without_a_bar_are_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(symbol: str) -> dict | None:
        return dict(_BAR) if symbol == "GOOD" else None

    monkeypatch.setattr(ingest_mod, "fetch_daily_bar_yfinance", fake_fetch)
    repo = _FakeRepo()

    stocks = await ingest_daily_bars(
        [
            IngestEntry("GOOD", "excel_watchlist"),
            IngestEntry("MISSING", "excel_watchlist"),
        ],
        repo,
    )

    assert [s.symbol for s in stocks] == ["GOOD"]
    assert [r["symbol"] for r in repo.rows] == ["GOOD"]
    assert repo.rows[0]["source_type"] == "excel_watchlist"


async def test_empty_entries_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_fetch(symbol: str) -> dict | None:
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(ingest_mod, "fetch_daily_bar_yfinance", fake_fetch)
    repo = _FakeRepo()

    assert await ingest_daily_bars([], repo) == []
    assert repo.rows == []
    assert called is False
