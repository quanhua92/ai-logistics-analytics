"""Curated-scenario tools — thin wrappers over the scenario runner.

These are the shared core; the LangChain and MCP adapters wrap them with
provider-specific tool schemas. Both adapters call these exact functions, so
the AI chat and external MCP clients return identical answers.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.scenarios import registry, runner


async def list_scenarios() -> list[dict[str, Any]]:
    """Catalog of every curated analytics scenario (id, group, title, question)."""
    return [
        {
            "id": s.id,
            "group": s.group,
            "title": s.title,
            "question": s.question,
            "chart_type": s.chart_type,
        }
        for s in registry.all_scenarios()
    ]


async def run_scenario(scenario_id: str, session: AsyncSession) -> dict[str, Any]:
    """Execute one curated scenario and return its data + chart spec + explanation."""
    if registry.get(scenario_id) is None:
        raise KeyError(f"unknown scenario: {scenario_id}")
    return await runner.run(scenario_id, session)
