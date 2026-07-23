"""Raw order listing tool.

The other tools only do aggregations; this one returns actual order rows so the
model can answer "list/show/recent orders" questions. Same allowlist discipline
as query_tool — the LLM sends a structured filter spec, never raw SQL.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order

# Filter field name -> ORM column / expression. Unknown names are rejected.
_FILTERS: dict[str, Any] = {
    "carrier": Order.carrier,
    "region": Order.region,
    "status": Order.status,
    "category": Order.product_category,
    "product_category": Order.product_category,
    "client": Order.client_id,
    "client_id": Order.client_id,
    "sku": Order.sku,
    "warehouse": Order.warehouse,
    "is_promo": Order.is_promo,
    "month": func.to_char(Order.order_date, "YYYY-MM"),
}

# Columns returned to the model/UI (focused, not all 17).
_COLS = (
    Order.order_id,
    Order.order_date,
    Order.delivery_date,
    Order.carrier,
    Order.status,
    Order.origin_city,
    Order.destination_city,
    Order.product_category,
    Order.quantity,
    Order.order_value_usd,
    Order.region,
)


def _ser(row: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row._mapping.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif isinstance(v, (int, float)):
            out[k] = round(float(v), 2) if isinstance(v, float) else v
        elif hasattr(v, "__float__"):  # Decimal
            out[k] = round(float(v), 2)
        else:
            out[k] = v
    return out


async def list_orders(spec: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
    """Return recent order rows matching the given filters.

    spec:
        filters:  dict of {field: value} — carrier|region|status|category|client|
                  sku|warehouse|is_promo|month (YYYY-MM, e.g. "2025-12")
        limit:    row cap (default 20, max 100)
    """
    filters = spec.get("filters") or {}
    limit = min(int(spec.get("limit") or 20), 100)

    stmt = select(*_COLS)
    for field, value in filters.items():
        if field not in _FILTERS:
            raise ValueError(f"unknown filter field: {field!r}")
        col = _FILTERS[field]
        if field == "is_promo" and isinstance(value, bool):
            value = 1 if value else 0
        stmt = stmt.where(col == value)

    stmt = stmt.order_by(Order.order_date.desc(), Order.id.desc()).limit(limit)
    result = await session.execute(stmt)
    rows = [_ser(r) for r in result.all()]

    return {
        "chart_type": "table",
        "data": rows,
        "explanation": {
            "metric": "order_rows",
            "dimensions": [],
            "method": "filtered order rows, newest first",
            "filters_used": [{"field": f, "op": "eq", "value": v} for f, v in filters.items()],
            "data_summary": {"row_count": len(rows)},
        },
    }
