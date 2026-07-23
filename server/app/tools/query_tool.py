"""Open-ended analytics query tool — a SAFE SQLAlchemy query builder.

The LLM never writes SQL. It sends a structured spec (metric / dimensions /
filters); this module validates every field against an allowlist and builds a
parameterized ORM query. Used by the LangChain and MCP adapters.
"""

from __future__ import annotations

from typing import Any
from decimal import Decimal

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order
from app.utils import chart_selector
from app.utils.explainability import build_explanation

# Dimension/field names -> ORM expressions. Everything the LLM can filter or
# group by MUST appear here; unknown names are rejected.
_DIMENSIONS: dict[str, Any] = {
    "carrier": Order.carrier,
    "region": Order.region,
    "status": Order.status,
    "category": Order.product_category,
    "product_category": Order.product_category,
    "warehouse": Order.warehouse,
    "client": Order.client_id,
    "client_id": Order.client_id,
    "sku": Order.sku,
    "is_promo": Order.is_promo,
    "month": func.to_char(Order.order_date, "YYYY-MM"),
    "day_of_week": cast(func.extract("dow", Order.order_date), Integer),
}

# Numeric fields available for sum/average.
_MEASURES: dict[str, Any] = {
    "order_value_usd": Order.order_value_usd,
    "quantity": Order.quantity,
    "unit_price_usd": Order.unit_price_usd,
}

# Chart types the LLM may request for an ad-hoc result. Others (multi-line,
# heatmap, forecast) need special data shapes only curated scenarios produce.
_CHART_TYPES = {
    "bar",
    "line",
    "area",
    "pie",
    "donut",
    "stat",
    "table",
    "stacked bar",
    "histogram",
}

_COMPLETED = ("delivered", "delayed")

# Operators understood by the filter clause.
_OPS = {
    "eq": lambda col, v: col == v,
    "ne": lambda col, v: col != v,
    "in": lambda col, v: col.in_(v if isinstance(v, list) else [v]),
    "gt": lambda col, v: col > v,
    "gte": lambda col, v: col >= v,
    "lt": lambda col, v: col < v,
    "lte": lambda col, v: col <= v,
}


def _metric_expr(metric: str, measure: str | None) -> Any:
    """Map a metric name to a SQL aggregate expression."""
    if metric == "count":
        return func.count(), "count of orders"
    if metric in ("sum", "average"):
        if measure not in _MEASURES:
            raise ValueError(f"metric '{metric}' needs a valid measure; got {measure!r}")
        col = _MEASURES[measure]
        return (func.sum(col) if metric == "sum" else func.avg(col)), f"{metric}({measure})"
    if metric == "delay_rate":
        expr = 100.0 * func.count().filter(Order.status == "delayed") / func.nullif(
            func.count().filter(Order.status.in_(_COMPLETED)), 0
        )
        return expr, "delay_rate"
    if metric == "on_time_rate":
        expr = 100.0 * func.count().filter(Order.status == "delivered") / func.nullif(
            func.count().filter(Order.status.in_(_COMPLETED)), 0
        )
        return expr, "on_time_rate"
    if metric == "delivery_time":
        return func.avg(Order.delivery_date - Order.order_date), "avg delivery days"
    raise ValueError(
        f"unknown metric {metric!r}; choose count|sum|average|delay_rate|on_time_rate|delivery_time"
    )


def _round(v: Any) -> Any:
    if isinstance(v, Decimal):
        return round(float(v), 2)
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    return v


async def query_analytics(spec: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
    """Build and run a validated analytics query from a structured spec.

    spec:
        metric:      one of count|sum|average|delay_rate|on_time_rate|delivery_time
        measure:     order_value_usd|quantity|unit_price_usd (for sum/average)
        group_by:    list of dimension names (may be empty for a single aggregate)
        filters:     list of {field, op, value}
        limit:       optional row cap (default 50, max 200)
        chart_type:  optional override — bar|line|area|pie|donut|stat|table|
                     stacked bar|histogram (else auto-selected from the data shape)
    """
    metric = spec.get("metric", "count")
    measure = spec.get("measure")
    dims = spec.get("group_by") or []
    filters = spec.get("filters") or []
    limit = min(int(spec.get("limit") or 50), 200)
    requested_chart = spec.get("chart_type")

    # Validate dimensions.
    bad_dims = [d for d in dims if d not in _DIMENSIONS]
    if bad_dims:
        raise ValueError(f"unknown dimension(s): {bad_dims}")

    metric_expr, metric_label = _metric_expr(metric, measure)

    # Build SELECT: one column per group-by dimension + the metric as "value".
    group_cols = [_DIMENSIONS[d] for d in dims]
    cols = group_cols + [metric_expr.label("value")]

    stmt = select(*cols)
    if dims:
        stmt = stmt.group_by(*group_cols)
        stmt = stmt.order_by(metric_expr.desc())
    stmt = stmt.limit(limit)

    # Apply validated filters.
    filter_records: list[dict[str, Any]] = []
    for f in filters:
        field, op, value = f.get("field"), f.get("op", "eq"), f.get("value")
        if field not in _DIMENSIONS:
            raise ValueError(f"unknown filter field: {field!r}")
        if op not in _OPS:
            raise ValueError(f"unknown operator: {op!r}")
        stmt = stmt.where(_OPS[op](_DIMENSIONS[field], value))
        filter_records.append({"field": field, "op": op, "value": value})

    result = await session.execute(stmt)
    rows = [{k: _round(v) for k, v in row._mapping.items()} for row in result.all()]

    if requested_chart is not None:
        if requested_chart not in _CHART_TYPES:
            raise ValueError(
                f"unknown chart_type: {requested_chart!r}; choose from {sorted(_CHART_TYPES)}"
            )
        chart_type = requested_chart
    else:
        chart_type = chart_selector.pick_chart_type(dims, rows)
    explanation = build_explanation(
        metric=metric_label,
        dimensions=dims,
        method=f"SQLAlchemy aggregate: {metric}" + (f" of {measure}" if measure else ""),
        filters=filter_records or None,
        row_count=len(rows),
    )

    return {
        "chart_type": chart_type,
        "data": rows,
        "explanation": explanation,
    }
