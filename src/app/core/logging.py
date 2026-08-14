"""
Structured logging setup.

Configures `structlog` so every log line is emitted as structured key/value
data (rendered as JSON in non-debug environments, or as colored console
output during local development). Call `configure_logging()` once, on
application startup, then use `get_logger(__name__)` anywhere in the code.
"""

import logging
import sys

import structlog

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure structlog + stdlib logging. Call once from the app lifespan."""
    settings = get_settings()

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level.upper(),
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    renderer = (
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structlog logger, e.g. `get_logger(__name__)`."""
    return structlog.get_logger(name)
