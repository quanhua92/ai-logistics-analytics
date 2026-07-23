from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app import schemas
from app.db import DbSession
from app.scenarios import registry, runner

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_KPI_SQL = """
SELECT
    COUNT(*)                                           AS total_orders,
    COUNT(*) FILTER (WHERE status = 'delivered')       AS delivered,
    COUNT(*) FILTER (WHERE status = 'delayed')         AS delayed,
    COUNT(*) FILTER (WHERE status = 'exception')       AS exceptions,
    COUNT(*) FILTER (WHERE status = 'in_transit')      AS in_transit,
    AVG(delivery_date - order_date)
        FILTER (WHERE delivery_date IS NOT NULL)       AS avg_delivery_days,
    SUM(order_value_usd)                               AS total_revenue
FROM orders
"""


@router.get("/kpis", response_model=schemas.KpiResponse)
async def kpis(db: DbSession):
    r = (await db.execute(text(_KPI_SQL))).one()
    completed = r.delivered + r.delayed
    on_time = 100.0 * r.delivered / completed if completed else 0.0
    return schemas.KpiResponse(
        total_orders=r.total_orders,
        delivered=r.delivered,
        delayed=r.delayed,
        exceptions=r.exceptions,
        in_transit=r.in_transit,
        on_time_rate=round(on_time, 1),
        avg_delivery_days=round(float(r.avg_delivery_days), 1) if r.avg_delivery_days is not None else None,
        total_revenue=float(r.total_revenue),
    )


@router.get("/scenarios", response_model=list[schemas.ScenarioMeta])
async def list_scenarios():
    return [
        schemas.ScenarioMeta(
            id=s.id, group=s.group, title=s.title, question=s.question, chart_type=s.chart_type
        )
        for s in registry.all_scenarios()
    ]


_KPI_TRENDS_SQL = """
SELECT
    TO_CHAR(order_date, 'YYYY-MM')                    AS month,
    COUNT(*)                                          AS total_orders,
    COUNT(*) FILTER (WHERE status = 'delivered')      AS delivered,
    COUNT(*) FILTER (WHERE status = 'delayed')        AS delayed,
    COUNT(*) FILTER (WHERE status = 'exception')      AS exceptions,
    COUNT(*) FILTER (WHERE status = 'in_transit')     AS in_transit,
    SUM(order_value_usd)                              AS revenue,
    AVG(delivery_date - order_date)
        FILTER (WHERE delivery_date IS NOT NULL)      AS avg_delivery
FROM orders
GROUP BY month
ORDER BY month
"""


def _series_and_delta(months: list[str], values: list[float]) -> dict:
    series = [{"month": m, "value": v} for m, v in zip(months, values)]
    delta = None
    if len(values) >= 2 and values[-2]:
        delta = round((values[-1] - values[-2]) / values[-2] * 100, 1)
    return {"series": series, "delta_pct": delta}


@router.get("/kpi-trends")
async def kpi_trends(db: DbSession):
    rows = (await db.execute(text(_KPI_TRENDS_SQL))).all()
    months = [r.month for r in rows]
    delivered = [r.delivered for r in rows]
    delayed = [r.delayed for r in rows]
    on_time = [
        round(100.0 * d / (d + dl), 1) if (d + dl) else 0.0
        for d, dl in zip(delivered, delayed)
    ]
    return {
        "total_orders": _series_and_delta(months, [r.total_orders for r in rows]),
        "delivered": _series_and_delta(months, delivered),
        "delayed": _series_and_delta(months, delayed),
        "exceptions": _series_and_delta(months, [r.exceptions for r in rows]),
        "in_transit": _series_and_delta(months, [r.in_transit for r in rows]),
        "on_time_rate": _series_and_delta(months, on_time),
        "total_revenue": _series_and_delta(months, [float(r.revenue or 0) for r in rows]),
        "avg_delivery_days": _series_and_delta(
            months, [round(float(r.avg_delivery or 0), 1) for r in rows]
        ),
    }


@router.get("/charts/{scenario_id}", response_model=schemas.ChartResponse)
async def chart(scenario_id: str, db: DbSession):
    if registry.get(scenario_id) is None:
        raise HTTPException(status_code=404, detail=f"unknown scenario: {scenario_id}")
    return await runner.run(scenario_id, db)
