"""Tests for `ChartinkSource` — HTTP and the Yahoo daily-bar fetch are stubbed."""

from datetime import date

import httpx
import pytest

import app.infrastructure.sources.daily_data_ingest as ingest_mod
from app.infrastructure.sources.chartink_source import ChartinkSource

_SCREENERS = {
    "screener_a": "( {cash} ( latest close > 0 ) )",
    "screener_b": "( {cash} ( latest volume > 0 ) )",
}

_BAR = {
    "trading_date": date(2026, 9, 8),
    "open": 100.0,
    "high": 110.0,
    "low": 99.0,
    "close": 105.0,
    "volume": 12345.0,
    "dividends": 0.0,
    "stock_splits": 0.0,
}


class _FakeRepo:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    async def upsert_daily_bars(self, rows: list[dict]) -> int:
        self.rows.extend(rows)
        return len(rows)


def _handler(rows_by_screener: dict[str, list[dict]]):
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/screener/":
            return httpx.Response(200, text='<meta name="csrf-token" content="test-token">')
        if request.url.path == "/screener/process":
            assert request.headers["x-csrf-token"] == "test-token"
            clause = httpx.QueryParams(request.content.decode())["scan_clause"]
            screener = next(k for k, v in _SCREENERS.items() if v == clause)
            return httpx.Response(200, json={"data": rows_by_screener.get(screener, [])})
        return httpx.Response(404)

    return httpx.MockTransport(handle)


@pytest.fixture(autouse=True)
def _stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.infrastructure.sources.chartink_source.CHARTINK_SCREENERS", _SCREENERS
    )
    monkeypatch.setattr(ingest_mod, "fetch_daily_bar_yfinance", lambda symbol: dict(_BAR))


async def test_each_matched_symbol_is_upserted_with_the_screener_as_source_type() -> None:
    repo = _FakeRepo()
    transport = _handler(
        {
            "screener_a": [
                {"nsecode": "reliance", "name": "Reliance Industries", "per_chg": "7.126"}
            ],
            "screener_b": [{"nsecode": "TCS", "name": "Tata Consultancy", "per_chg": -0.4}],
        }
    )
    source = ChartinkSource(repo, transport=transport)

    stocks = await source.fetch_stocks()

    assert {(r["symbol"], r["source_type"]) for r in repo.rows} == {
        ("RELIANCE", "screener_a"),
        ("TCS", "screener_b"),
    }
    assert all(r["close"] == 105.0 and r["trading_date"] == date(2026, 9, 8) for r in repo.rows)
    by_symbol = {r["symbol"]: r for r in repo.rows}
    assert by_symbol["RELIANCE"]["percent_change"] == 7.13  # coerced from str + rounded
    assert by_symbol["TCS"]["percent_change"] == -0.4
    assert {(s.symbol, s.source_type) for s in stocks} == {
        ("RELIANCE", "screener_a"),
        ("TCS", "screener_b"),
    }


async def test_same_symbol_from_two_screeners_produces_two_rows() -> None:
    repo = _FakeRepo()
    transport = _handler(
        {
            "screener_a": [{"nsecode": "RELIANCE", "name": "Reliance Industries"}],
            "screener_b": [{"nsecode": "RELIANCE", "name": "Reliance Industries"}],
        }
    )

    await ChartinkSource(repo, transport=transport).fetch_stocks()

    assert sorted(r["source_type"] for r in repo.rows) == ["screener_a", "screener_b"]
    assert {r["symbol"] for r in repo.rows} == {"RELIANCE"}


async def test_unknown_screener_writes_nothing() -> None:
    repo = _FakeRepo()
    source = ChartinkSource(repo, ["does_not_exist"], transport=_handler({}))

    assert await source.fetch_stocks() == []
    assert repo.rows == []


async def test_scan_error_skips_that_screener_without_failing_the_run() -> None:
    repo = _FakeRepo()

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/screener/":
            return httpx.Response(200, text='<meta name="csrf-token" content="test-token">')
        return httpx.Response(200, json={"scan_error": "bad clause"})

    source = ChartinkSource(repo, ["screener_a"], transport=httpx.MockTransport(handle))

    assert await source.fetch_stocks() == []
    assert repo.rows == []


async def test_missing_csrf_token_raises() -> None:
    repo = _FakeRepo()

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>no token</html>")

    source = ChartinkSource(repo, transport=httpx.MockTransport(handle))

    with pytest.raises(RuntimeError, match="CSRF token"):
        await source.fetch_stocks()
