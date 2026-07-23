"""Forecast endpoints — pure statistics, no AI. Open (no key gate, no tokens)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app import schemas
from app.db import DbSession
from app.services import forecasting

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("/categories", response_model=list[str])
async def categories(db: DbSession) -> list[str]:
    """Product categories available for demand forecasting."""
    return await forecasting.list_categories(db)


@router.get("", response_model=schemas.ForecastResponse)
async def forecast(
    db: DbSession,
    category: str = Query(..., description="Product category to forecast"),
    horizon: int = Query(4, ge=1, le=12, description="Months to project forward (1-12)"),
) -> schemas.ForecastResponse:
    """Forecast monthly demand for a category (statistics only — no LLM)."""
    cats = await forecasting.list_categories(db)
    if category not in cats:
        raise HTTPException(status_code=404, detail=f"unknown category: {category}")
    result = await forecasting.forecast(category, horizon, db)
    return schemas.ForecastResponse(**result)
