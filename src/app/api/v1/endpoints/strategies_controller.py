"""
Strategies endpoints.

Thin HTTP adapters: each handler resolves its dependencies via `Depends`
(see `app/api/deps.py`), delegates to a service, and maps the result to a
Pydantic schema. No business logic lives here.
"""

from fastapi import APIRouter, HTTPException

from app.api.deps import StockServiceDep, StrategyRegistryDep, StrategyRunnerServiceDep
from app.schemas.strategy_schema import StrategyMatchRead, StrategyRunRequest

router = APIRouter()


@router.post("/strategies/run", response_model=list[StrategyMatchRead])
async def run_strategies(
    request: StrategyRunRequest,
    stock_service: StockServiceDep,
    strategy_runner: StrategyRunnerServiceDep,
    strategy_registry: StrategyRegistryDep,
) -> list[StrategyMatchRead]:
    """Evaluate persisted stocks against named strategies (see `infrastructure/strategies/`)."""
    strategies = []
    for strategy_name in request.strategy_names:
        strategy_factory = strategy_registry.get(strategy_name)
        if strategy_factory is None:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy_name}")
        strategies.append(strategy_factory())

    stocks = await stock_service.list_stocks()
    matches = await strategy_runner.run(strategies, stocks)
    return [
        StrategyMatchRead(
            stock_symbol=match.stock.symbol,
            strategy_name=match.strategy_name,
            matched=match.matched,
            details=match.details,
        )
        for match in matches
    ]
