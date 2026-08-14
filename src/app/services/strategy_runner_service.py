"""
Strategy runner service.

Runs one or more strategy plugins against a list of stocks and collects
their matches. Doesn't import any concrete strategy class — it just expects
each strategy to have a `name` property and an async `evaluate()` method,
matching the shapes in `app/infrastructure/strategies/`. That keeps this
file unchanged when a new strategy is added.
"""

from app.core.logging import get_logger
from app.domain.entities.stock import Stock, StrategyMatch

logger = get_logger(__name__)


class StrategyRunnerService:
    """Application service for evaluating stocks against strategies."""

    async def run(self, strategies: list, stocks: list[Stock]) -> list[StrategyMatch]:
        """Evaluate `stocks` against every strategy in `strategies` and return all matches."""
        all_matches: list[StrategyMatch] = []
        for strategy in strategies:
            logger.info("running_strategy", strategy=strategy.name, stock_count=len(stocks))
            all_matches.extend(await strategy.evaluate(stocks))
        return all_matches
