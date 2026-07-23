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


@router.get("/charts/{scenario_id}", response_model=schemas.ChartResponse)
async def chart(scenario_id: str, db: DbSession):
    if registry.get(scenario_id) is None:
        raise HTTPException(status_code=404, detail=f"unknown scenario: {scenario_id}")
    return await runner.run(scenario_id, db)
