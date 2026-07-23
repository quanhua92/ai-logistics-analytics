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


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatTurn] = []
    conversation_id: str = ""


class ChatResponse(BaseModel):
    answer: str
    chart_type: str | None = None
    chart_data: list[dict[str, Any]] | None = None
    explanation: dict[str, Any] | None = None
    scenario_id: str | None = None
    title: str | None = None


class HistoricalPoint(BaseModel):
    month: str
    quantity: int


class ForecastPoint(BaseModel):
    month: str
    quantity: float
    linear: float | None = None
    moving_average: float | None = None


class ForecastRecommendation(BaseModel):
    peak_forecast_units: int
    safety_stock_units: int
    note: str


class ForecastReadiness(BaseModel):
    mean_monthly_quantity: float
    std_dev: float
    data_points: int


class ForecastResponse(BaseModel):
    category: str
    horizon_months: int
    historical: list[HistoricalPoint]
    forecast: list[ForecastPoint]
    recommendation: ForecastRecommendation
    methodology: str
    readiness: ForecastReadiness
