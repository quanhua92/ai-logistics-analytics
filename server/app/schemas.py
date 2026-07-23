from typing import Any

from pydantic import BaseModel


class ScenarioMeta(BaseModel):
    id: str
    group: str
    title: str
    question: str
    chart_type: str


class ChartResponse(BaseModel):
    id: str
    title: str
    question: str
    chart_type: str
    data: list[dict[str, Any]]
    explanation: dict[str, Any]


class KpiResponse(BaseModel):
    total_orders: int
    delivered: int
    delayed: int
    exceptions: int
    in_transit: int
    on_time_rate: float
    avg_delivery_days: float | None
    total_revenue: float
