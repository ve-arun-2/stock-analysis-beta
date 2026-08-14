"""
Strategy registry.

A tiny factory that maps a strategy name to a constructed strategy instance.
Every strategy implements the same shape by convention (a `name` property and
an async `evaluate()` method) rather than a formal interface. This is the
single place that needs a new line added when a new strategy plugin is
introduced — `app/api/deps.py` and the service layer never need to change.
"""

from collections.abc import Callable

from app.infrastructure.strategies.chartink_strategy import ChartinkStrategy
from app.infrastructure.strategies.ema_strategy import EMAPeriod, EMAStrategy
from app.infrastructure.strategies.excel_watchlist_strategy import ExcelWatchlistStrategy

StrategyPlugin = EMAStrategy | ChartinkStrategy | ExcelWatchlistStrategy


def build_strategy_registry() -> dict[str, Callable[[], StrategyPlugin]]:
    """Return a mapping of strategy name -> factory function for that strategy."""
    return {
        "ema_20": lambda: EMAStrategy(EMAPeriod.SHORT),
        "ema_50": lambda: EMAStrategy(EMAPeriod.MEDIUM),
        "ema_200": lambda: EMAStrategy(EMAPeriod.LONG),
        "chartink_default": lambda: ChartinkStrategy(screener_name="default"),
        "excel_watchlist_default": lambda: ExcelWatchlistStrategy(watchlist_name="default"),
    }
