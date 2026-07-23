"""Forecast tool — wraps the pure-statistics forecasting service.

Same service powers the ``/api/forecast`` page; the AI merely *decides* to call
this tool. No LLM is involved in the actual computation.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import forecasting


async def list_categories(session: AsyncSession) -> list[str]:
    """Product categories available for forecasting."""
    return await forecasting.list_categories(session)


async def forecast_demand(
    category: str, horizon_months: int, session: AsyncSession
) -> dict[str, Any]:
    """Forecast monthly demand for ``category`` over ``horizon_months`` (1-12)."""
    return await forecasting.forecast(category, horizon_months, session)
