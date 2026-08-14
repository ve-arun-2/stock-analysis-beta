"""
Domain-level exceptions.

These are raised by the domain/service layers and are transport-agnostic
(they know nothing about HTTP). The API layer (see `app/api/error_handlers.py`
once added) is responsible for translating them into HTTP responses. This
keeps the domain layer free of any FastAPI/HTTP concerns.
"""


class AppError(Exception):
    """Base class for all application-specific errors."""


class NotFoundError(AppError):
    """Raised when a requested entity does not exist."""


class ValidationError(AppError):
    """Raised when input fails a domain rule (distinct from Pydantic's schema validation)."""


class DataSourceError(AppError):
    """Raised when a `StockSource` plugin fails to fetch or parse data."""


class StrategyExecutionError(AppError):
    """Raised when a `Strategy` plugin fails while evaluating stocks."""
