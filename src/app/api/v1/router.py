"""Aggregates every v1 endpoint router into a single `api_router`."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, stocks_controller, strategies_controller

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(stocks_controller.router, tags=["stocks"])
api_router.include_router(strategies_controller.router,  tags=["strategies"])
