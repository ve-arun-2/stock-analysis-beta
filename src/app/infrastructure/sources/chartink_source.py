"""
Chartink screener source.

Fetches stocks matching a saved Chartink screener via HTTP (httpx). Phase 1
only wires up the shape; the actual request/response handling is added later.
"""

import httpx

from app.domain.entities.stock import Stock


class ChartinkSource:
    """Fetches stocks matching a Chartink screener clause."""

    def __init__(self, base_url: str, screener_clause: str, http_client: httpx.AsyncClient) -> None:
        self._base_url = base_url
        self._screener_clause = screener_clause
        self._http_client = http_client

    @property
    def name(self) -> str:
        return "chartink"

    async def fetch_stocks(self) -> list[Stock]:
        # Phase 2: POST `self._screener_clause` to Chartink's screener endpoint
        # via `self._http_client` and map the response rows to Stock entities.
        raise NotImplementedError("Chartink integration will be implemented in a later phase.")
