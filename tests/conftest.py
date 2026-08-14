"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Generator[TestClient]:
    """A `TestClient` that runs the app's lifespan (startup/shutdown) for each test."""
    with TestClient(app) as test_client:
        yield test_client
