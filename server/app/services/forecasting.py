"""Demand forecasting — pure statistics, no LLM.

Aggregates historical order quantity by category x month and projects forward
using three complementary methods (linear regression, moving average, exponential
smoothing). The strongest signal is surfaced as the primary forecast; the others
are reported for cross-checking.

This service is independent of the AI layer: the ``/api/forecast`` page and the
``forecast_demand`` tool both call :func:`forecast`.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order

_START_YEAR = 2025
_MONTHS = [f"{_START_YEAR}-{m:02d}" for m in range(1, 13)]


def _fc_linear(y: list[float], horizon: int) -> list[float]:
    n = len(y)
    x = list(range(n))
    xbar = sum(x) / n
    ybar = sum(y) / n
    denom = sum((xi - xbar) ** 2 for xi in x) or 1
    slope = sum((xi - xbar) * (yi - ybar) for xi, yi in zip(x, y)) / denom
    intercept = ybar - slope * xbar
    return [intercept + slope * (n + i) for i in range(horizon)]


def _fc_ma(y: list[float], horizon: int, window: int = 3) -> list[float]:
    tail = y[-window:] if len(y) >= window else y
    ma = sum(tail) / len(tail) if tail else 0.0
    return [ma] * horizon


def _fc_es(y: list[float], horizon: int, alpha: float = 0.3) -> list[float]:
    if not y:
        return [0.0] * horizon
    level = y[0]
    for h in y[1:]:
        level = alpha * h + (1 - alpha) * level
    return [level] * horizon


async def _category_series(category: str, session: AsyncSession) -> list[float]:
    """Monthly quantity for ``category`` across Jan-Dec 2025."""
    rows = (
        await session.execute(
            select(Order.order_date, Order.quantity).where(
                Order.product_category == category
            )
        )
    ).all()
    by_month: dict[str, int] = defaultdict(int)
    for order_date, qty in rows:
        key = order_date.strftime("%Y-%m")
        by_month[key] += int(qty)
    return [float(by_month.get(m, 0)) for m in _MONTHS]


async def list_categories(session: AsyncSession) -> list[str]:
    rows = (
        await session.execute(
            select(Order.product_category)
            .distinct()
            .order_by(Order.product_category)
        )
    ).all()
    return [r[0] for r in rows]


async def forecast(
    category: str, horizon: int, session: AsyncSession
) -> dict[str, Any]:
    """Forecast monthly demand for ``category`` over ``horizon`` months."""
    horizon = max(1, min(horizon, 12))
    y = await _category_series(category, session)
    n = len(y)

    mean = sum(y) / n if n else 0.0
    std = math.sqrt(sum((v - mean) ** 2 for v in y) / n) if n else 0.0

    lin = _fc_linear(y, horizon)
    ma = _fc_ma(y, horizon)
    es = _fc_es(y, horizon)

    # Primary forecast: exponential smoothing (reacts to recent change) floored at 0.
    primary = [max(0.0, round(v, 1)) for v in es]

    historical = [{"month": m, "quantity": int(y[i])} for i, m in enumerate(_MONTHS)]
    last_month_idx = len(_MONTHS) - 1
    forecast_points = []
    for i in range(horizon):
        m_idx = last_month_idx + 1 + i
        year = _START_YEAR + (m_idx // 12)
        month = (m_idx % 12) + 1
        forecast_points.append(
            {
                "month": f"{year}-{month:02d}",
                "quantity": primary[i],
                "linear": round(max(0.0, lin[i]), 1),
                "moving_average": round(ma[i], 1),
            }
        )

    peak = max(primary) if primary else 0.0
    safety_stock = math.ceil(peak * 1.2)

    return {
        "category": category,
        "horizon_months": horizon,
        "historical": historical,
        "forecast": forecast_points,
        "recommendation": {
            "peak_forecast_units": math.ceil(peak),
            "safety_stock_units": safety_stock,
            "note": f"Stock ~{safety_stock} units for the peak forecast month "
            f"(peak + 20% safety margin).",
        },
        "methodology": (
            "Three statistical methods computed on monthly quantity (Jan-Dec 2025): "
            "linear regression (trend), 3-month moving average, and exponential "
            "smoothing (alpha=0.3). The exponential-smoothing projection is used as "
            "the primary forecast because it weights recent demand more heavily. "
            "No machine learning is involved."
        ),
        "readiness": {
            "mean_monthly_quantity": round(mean, 1),
            "std_dev": round(std, 1),
            "data_points": n,
        },
    }
