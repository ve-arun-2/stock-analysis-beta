"""
Chartink screener source.

Runs the saved Chartink screeners listed in `chartink_screeners.py`
(`CHARTINK_SCREENERS`), then for every matched symbol pulls the latest daily
bar from Yahoo Finance and upserts it into `stock_daily_data` with
`source_type` set to the screener key. The same symbol returned by two
screeners becomes two rows (one per screener).

Chartink has no official API. The flow mirrors what the website itself does:
  1. GET /screener/ once to pick up a session cookie + CSRF token.
  2. POST each screener's `scan_clause` to /screener/process with that token.
"""

import asyncio
import re

import httpx

from app.core.logging import get_logger
from app.domain.entities.chartink_screeners import CHARTINK_SCREENERS
from app.domain.entities.stock import Stock
from app.infrastructure.repositories.stock_daily_data_repository import (
    StockDailyDataRepository,
)
from app.infrastructure.sources.daily_data_ingest import IngestEntry, ingest_daily_bars

logger = get_logger(__name__)

CHARTINK_BASE_URL = "https://chartink.com"

_SCREENER_PAGE = "/screener/"
_SCREENER_PROCESS = "/screener/process"
_REQUEST_TIMEOUT = 30.0

_CSRF_RE = re.compile(
    r'<meta\s+name="csrf-token"\s+content="([^"]+)"',
    re.IGNORECASE,
)

_BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def _to_pct(value: object) -> float | None:
    """Chartink's `per_chg` arrives as a number or a string — coerce and round."""
    try:
        return round(float(value), 2)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class ChartinkSource:
    """Collects symbols matched by one or more Chartink screeners into `stock_daily_data`."""

    def __init__(
        self,
        stock_daily_data_repo: StockDailyDataRepository,
        screener_names: list[str] | None = None,
        *,
        base_url: str = CHARTINK_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._stock_daily_data_repo = stock_daily_data_repo
        # None -> run every screener defined in CHARTINK_SCREENERS.
        self._screener_names = (
            list(CHARTINK_SCREENERS) if screener_names is None else screener_names
        )
        self._base_url = base_url.rstrip("/")
        self._transport = transport  # injected in tests; None uses the real network

    @property
    def name(self) -> str:
        return "chartink"

    async def fetch_stocks(self) -> list[Stock]:
        clauses = self._resolve_clauses()
        if not clauses:
            logger.warning("chartink_no_screeners", requested=self._screener_names)
            return []

        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=_REQUEST_TIMEOUT,
            follow_redirects=True,
            headers=_BASE_HEADERS,
            transport=self._transport,
        ) as client:
            csrf_token = await self._fetch_csrf_token(client)
            results = await asyncio.gather(
                *(
                    self._run_screener(client, csrf_token, label, clause)
                    for label, clause in clauses.items()
                ),
                return_exceptions=True,
            )

        # One entry per (symbol, screener). A symbol hit by two screeners yields
        # two entries -> two `stock_daily_data` rows with different source_type.
        entries: dict[tuple[str, str], IngestEntry] = {}
        for label, outcome in zip(clauses, results, strict=True):
            if isinstance(outcome, Exception):
                logger.error("chartink_screener_failed", screener=label, error=str(outcome))
                continue
            for symbol, company_name, percent_change in outcome:
                entries.setdefault(
                    (symbol, label),
                    IngestEntry(
                        symbol=symbol,
                        source_type=label,
                        company_name=company_name,
                        percent_change=percent_change,
                    ),
                )

        logger.info("chartink_symbols_matched", screeners=list(clauses), count=len(entries))
        return await ingest_daily_bars(entries.values(), self._stock_daily_data_repo)

    def _resolve_clauses(self) -> dict[str, str]:
        """Map each requested screener label to its scan clause, skipping unknowns."""
        clauses: dict[str, str] = {}
        for label in self._screener_names:
            clause = CHARTINK_SCREENERS.get(label)
            if not clause:
                logger.warning("chartink_unknown_screener", screener=label)
                continue
            clauses[label] = clause
        return clauses

    async def _fetch_csrf_token(self, client: httpx.AsyncClient) -> str:
        response = await client.get(_SCREENER_PAGE)
        response.raise_for_status()
        match = _CSRF_RE.search(response.text)
        if not match:
            raise RuntimeError("Could not find the Chartink CSRF token on the screener page.")
        return match.group(1)

    async def _run_screener(
        self,
        client: httpx.AsyncClient,
        csrf_token: str,
        label: str,
        clause: str,
    ) -> list[tuple[str, str, float | None]]:
        """Return (symbol, company_name, percent_change) for every matched row."""
        response = await client.post(
            _SCREENER_PROCESS,
            data={"scan_clause": clause},
            headers={
                "x-csrf-token": csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self._base_url}{_SCREENER_PAGE}",
            },
        )
        response.raise_for_status()
        payload = response.json()

        if payload.get("scan_error"):
            raise RuntimeError(f"Chartink rejected the scan clause: {payload['scan_error']}")

        rows = payload.get("data", []) or []
        logger.info("chartink_screener_result", screener=label, row_count=len(rows))

        matched: list[tuple[str, str, float | None]] = []
        for row in rows:
            code = row.get("nsecode")
            if not code:
                continue
            symbol = str(code).strip().upper()
            matched.append((symbol, row.get("name") or symbol, _to_pct(row.get("per_chg"))))
        return matched
