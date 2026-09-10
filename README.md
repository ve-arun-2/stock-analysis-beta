# Stock Analysis Platform

A long-term **stock analysis platform** — not a trading bot. It collects stocks from
multiple pluggable sources, evaluates them with pluggable strategies, and (in a future
phase) layers an Agentic AI on top for research and recommendations.

**Phase 1 status:** architecture and boilerplate only. Every plugin (source/strategy) is
wired up end-to-end but its actual logic is a stub that raises `NotImplementedError` —
see the "What's stubbed vs. real" section below.

## Why the code is organized this way

The project follows **Clean Architecture**: dependencies only point inward, toward the
domain. Outer layers (API, infrastructure) depend on inner layers (domain), never the
reverse. This is what makes "swap the database" or "add a new data source" a
localized change instead of a rewrite.

```
src/app/
├── domain/            ← innermost layer: business entities
│   └── entities/       Plain Python objects (Stock, StrategyMatch). No framework imports.
│
├── infrastructure/     ← outermost layer: concrete sources, strategies, and persistence
│   ├── database/        SQLAlchemy engine, session, declarative Base, ORM models.
│   ├── repositories/     SqlAlchemyStockRepository (SQLAlchemy <-> Stock entity mapping).
│   ├── sources/          Source plugins (Excel, Chartink, Yahoo Finance) + registry.
│   └── strategies/       Strategy plugins (EMA, Chartink, Excel watchlist) + registry.
│
├── services/           ← application layer: orchestrates sources/strategies/repositories
│   ├── stock_service.py            Fetch from a source, persist via a repository.
│   └── strategy_runner_service.py  Run N strategies against a stock list.
│
├── ai/                 ← reserved for the future Agentic AI layer
│   └── agents/           Empty. Concrete agents will live here, using services as tools.
│
├── api/                ← HTTP adapter layer
│   ├── deps.py           The ONLY place that wires concrete implementations together.
│   └── v1/                Versioned routers + one module per resource under endpoints/.
│
├── schemas/            Pydantic request/response DTOs (distinct from entities and ORM models).
├── core/               Settings, structured logging, and shared exceptions.
└── main.py             FastAPI app: lifespan, middleware, router mounting.
```

**No `interfaces/` (ABC) layer for now.** Every source implements a `name`
property and an async `fetch_stocks()`; every strategy implements a `name`
property and an async `evaluate()`. That's a convention, not an enforced
contract — kept this way deliberately to avoid extra abstraction while still
learning the rest of the stack. It can be formalized with `abc.ABC` (or
`typing.Protocol`) later without touching how the registries or services work.

Three representations of "a stock" exist on purpose and are never merged:

| Representation | File | Concern |
|---|---|---|
| `Stock` (entity) | `domain/entities/stock.py` | Business rules, framework-independent |
| `StockModel` (ORM) | `infrastructure/database/models/stock_model.py` | How a stock is stored in PostgreSQL |
| `StockRead` (schema) | `schemas/stock.py` | How a stock looks over HTTP |

## The plugin pattern (Open/Closed Principle)

Adding a new **data source** or **strategy** never requires touching an existing file:

1. Create a new class in a new module under `infrastructure/sources/` or
   `infrastructure/strategies/`, matching the existing convention (a `name`
   property, plus `fetch_stocks()`/`evaluate()`).
2. Register it with one new line in that folder's `registry.py`.

The service layer and API endpoints depend only on the registries — they have no idea
how many sources or strategies exist, or how any of them work internally.

## What's stubbed vs. real (Phase 1)

**Wired up and working:**
- FastAPI app boots, `/api/v1/health` responds, dependency injection resolves end-to-end.
- `GET /api/v1/stocks` and `POST /api/v1/stocks/collect` reach the service/repository layer.
- `POST /api/v1/strategies/run` reaches the strategy runner.
- Database session, ORM model, and Alembic migration setup are functional against a real
  PostgreSQL instance.

**Intentionally stubbed** (raise `NotImplementedError` until a later phase):
- `YahooFinanceSource.fetch_stocks`
- `EMAStrategy.evaluate`, `ChartinkStrategy.evaluate`, `ExcelWatchlistStrategy.evaluate`
- The entire `ai/agents/` package

## Running locally

```bash
# Install dependencies (editable + dev extras)
pip install -e ".[dev]"

# Start PostgreSQL (or use docker compose up db)
cp .env.example .env   # then edit DATABASE_URL if needed

# Apply migrations
alembic upgrade head

# Run the API with auto-reload
uvicorn app.main:app --reload --app-dir src
```

Or with Docker: `docker compose up --build`.

Interactive API docs: `http://localhost:8000/docs`.

## Running tests

```bash
pytest
```

## Linting/formatting

```bash
ruff check .
black .
```

## Creating a migration

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```
