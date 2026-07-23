from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.scenarios import registry


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


async def run(scenario_id: str, session: AsyncSession) -> dict[str, Any]:
    scenario = registry.get(scenario_id)
    if scenario is None:
        raise KeyError(scenario_id)

    result = await session.execute(text(scenario.sql))
    rows = [{k: _jsonable(v) for k, v in row._mapping.items()} for row in result.all()]

    return {
        "id": scenario.id,
        "title": scenario.title,
        "question": scenario.question,
        "chart_type": scenario.chart_type,
        "data": rows,
        "explanation": scenario.explanation,
    }
