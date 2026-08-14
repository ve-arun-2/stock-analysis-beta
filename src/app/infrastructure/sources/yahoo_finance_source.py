"""
Yahoo Finance source.

Fetches stock quotes/history from Yahoo Finance via HTTP (httpx). Phase 1
only wires up the shape; the actual request/response handling is added later.
"""

import httpx

from app.domain.entities.stock import Stock


class YahooFinanceSource:
    """Fetches stocks/quotes from Yahoo Finance."""

    def __init__(self, base_url: str, symbols: list[str], http_client: httpx.AsyncClient) -> None:
        self._base_url = base_url
        self._symbols = symbols
        self._http_client = http_client

    @property
    def name(self) -> str:
        return "yahoo_finance"

    async def fetch_stocks(self) -> list[Stock]:
        # Phase 2: call Yahoo Finance's quote endpoint via `self._http_client`
        # for each symbol in `self._symbols` and map the results to Stock entities.
        raise NotImplementedError("Yahoo Finance integration will be implemented in a later phase.")
