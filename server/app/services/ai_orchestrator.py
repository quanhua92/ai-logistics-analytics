"""AI orchestrator — natural-language logistics questions via tool calling.

Architecture: one scenario registry + a safe query builder + a stats forecaster
form the shared tool core. The LLM (any OpenAI-compatible model via
ChatOpenRouter) only *decides which tool to call* and then narrates the result.
It never writes SQL and never fabricates numbers — every figure it cites comes
from a tool call.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.scenarios import registry
from app.tools import forecast_tool, query_tool, scenario_tool

_MAX_STEPS = 6

_SYSTEM_HEADER = """\
You are the analytics assistant for a logistics company. You answer questions
about orders, deliveries, carriers, regions, products, and revenue using a set
of read-only analytics tools backed by a PostgreSQL database.

RULES
1. ALWAYS call a tool before stating any number, ranking, or trend. Never
   fabricate or recall figures from memory.
2. Prefer the curated `run_scenario` tool (fast, pre-validated) over the ad-hoc
   `query_analytics` tool. There is a curated scenario for most common questions.
3. If you are unsure whether a scenario exists or what its parameters are, call
   `list_scenarios` first.
4. After the tool returns, give a concise, plain-English answer. Call out the
   single most important insight, then supporting detail. Note the chart type
   the data maps to when useful.
5. If the question is ambiguous, ask ONE short clarifying question before
   running any tool.
6. For forecasts, use `forecast_demand` (pure statistics — no guessing).

You have these tools:
- list_scenarios(): the full curated catalog (id + the question each answers).
- run_scenario(scenario_id): run one curated scenario by id.
- query_analytics(metric, measure, group_by, filters, limit): ad-hoc aggregation
  when no curated scenario fits. metric ∈ count|sum|average|delay_rate|
  on_time_rate|delivery_time; measure ∈ order_value_usd|quantity|unit_price_usd
  (only for sum/average); group_by ∈ carrier|region|status|category|warehouse|
  client|sku|is_promo|month|day_of_week; filters is a list of
  {field, op, value} with op ∈ eq|ne|in|gt|gte|lt|lte.
- list_forecast_categories(): product categories available for forecasting.
- forecast_demand(category, horizon_months): forecast monthly demand.
"""


def build_system_prompt() -> str:
    """Static header + the live scenario catalog grouped by section."""
    lines = [_SYSTEM_HEADER, "CURATED SCENARIO CATALOG (use the id with run_scenario):"]
    groups: dict[str, list] = {}
    for s in registry.all_scenarios():
        groups.setdefault(s.group, []).append(s)
    for group, scns in groups.items():
        lines.append(f"\n[{group}]")
        for s in scns:
            lines.append(f"  - {s.id}: {s.question}")
    return "\n".join(lines)


def _make_llm() -> ChatOpenRouter:
    return ChatOpenRouter(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        temperature=0,
    )


def _make_tools(session: AsyncSession) -> list:
    """Build LangChain tools, closing over the request-scoped DB session."""

    @tool
    async def list_scenarios() -> list[dict]:
        """List every curated analytics scenario with its id and the question it answers."""
        return await scenario_tool.list_scenarios()

    @tool
    async def run_scenario(scenario_id: str) -> dict:
        """Run one curated analytics scenario by id. Returns data, chart_type, explanation."""
        return await scenario_tool.run_scenario(scenario_id, session)

    @tool
    async def query_analytics(
        metric: str,
        measure: str | None = None,
        group_by: list[str] | None = None,
        filters: list[dict] | None = None,
        limit: int | None = None,
    ) -> dict:
        """Run an ad-hoc aggregation when no curated scenario fits. See tool rules above."""
        return await query_tool.query_analytics(
            {
                "metric": metric,
                "measure": measure,
                "group_by": group_by,
                "filters": filters,
                "limit": limit,
            },
            session,
        )

    @tool
    async def list_forecast_categories() -> list[str]:
        """List the product categories available for demand forecasting."""
        return await forecast_tool.list_categories(session)

    @tool
    async def forecast_demand(category: str, horizon_months: int) -> dict:
        """Forecast monthly demand for a product category over 1-12 months (pure statistics)."""
        return await forecast_tool.forecast_demand(category, horizon_months, session)

    return [list_scenarios, run_scenario, query_analytics, list_forecast_categories, forecast_demand]


def _capture_chart(tool_name: str, result: Any) -> dict | None:
    """Normalize a tool result into a frontend chart payload, if it has one."""
    if not isinstance(result, dict):
        return None
    if tool_name == "run_scenario":
        return {
            "scenario_id": result.get("id"),
            "title": result.get("title"),
            "chart_type": result.get("chart_type"),
            "data": result.get("data"),
            "explanation": result.get("explanation"),
        }
    if tool_name == "query_analytics":
        return {
            "chart_type": result.get("chart_type"),
            "data": result.get("data"),
            "explanation": result.get("explanation"),
        }
    if tool_name == "forecast_demand":
        hist = [
            {**p, "type": "historical"} for p in result.get("historical", [])
        ]
        fc = [{**p, "type": "forecast"} for p in result.get("forecast", [])]
        return {
            "chart_type": "forecast",
            "data": hist + fc,
            "explanation": {
                "metric": "forecasted_quantity",
                "category": result.get("category"),
                "horizon_months": result.get("horizon_months"),
                "methodology": result.get("methodology"),
                "recommendation": result.get("recommendation"),
            },
        }
    return None


def _tool_label(name: str, args: dict) -> str:
    """Human-readable label for a tool invocation, surfaced to the UI."""
    if name == "run_scenario":
        sid = args.get("scenario_id")
        sc = registry.get(sid) if sid else None
        return sc.title if sc else f"Running {sid}"
    if name == "query_analytics":
        metric = args.get("metric", "data")
        dims = args.get("group_by") or []
        return f"Querying {metric}" + (f" by {', '.join(dims)}" if dims else "")
    if name == "forecast_demand":
        cat = args.get("category", "?")
        horizon = args.get("horizon_months")
        return f"Forecasting {cat}" + (f" ({horizon}mo)" if horizon else "")
    if name == "list_scenarios":
        return "Loading scenario catalog"
    if name == "list_forecast_categories":
        return "Loading categories"
    return name


async def ask_stream(question: str, session: AsyncSession):
    """Async generator yielding SSE event dicts.

    Events: status, tool, token, done, error. The ``done`` event carries the
    same payload shape as :func:`ask` so streaming and non-streaming clients
    render identically.
    """
    if not settings.openrouter_api_key:
        yield {"type": "error", "detail": "OPENROUTER_API_KEY is not set — add it to server/.env"}
        return

    llm = _make_llm()
    tools = _make_tools(session)
    tool_map = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    messages: list = [SystemMessage(content=build_system_prompt()), HumanMessage(content=question)]
    chart_payload: dict | None = None
    acc = None

    yield {"type": "status", "step": "thinking"}
    try:
        for _ in range(_MAX_STEPS):
            acc = None
            async for chunk in llm_with_tools.astream(messages):
                # Stream content deltas as tokens (final-answer text).
                if chunk.content:
                    yield {"type": "token", "delta": chunk.content}
                acc = chunk if acc is None else acc + chunk
            if acc is None:
                break
            messages.append(acc)
            if not getattr(acc, "tool_calls", None):
                break
            for tc in acc.tool_calls:
                name, args, call_id = tc["name"], tc["args"], tc["id"]
                yield {"type": "tool", "name": name, "label": _tool_label(name, args)}
                try:
                    result = await tool_map[name].ainvoke(args)
                except Exception as exc:  # surface tool errors to the model so it can recover
                    result = {"error": f"{type(exc).__name__}: {exc}"}
                captured = _capture_chart(name, result)
                if captured:
                    chart_payload = captured
                messages.append(
                    ToolMessage(content=json.dumps(result, default=str), tool_call_id=call_id)
                )
    except Exception as exc:
        yield {"type": "error", "detail": f"{type(exc).__name__}: {exc}"}
        return

    answer = (acc.content if acc and acc.content else "").strip() or "(no answer)"
    yield {
        "type": "done",
        "answer": answer,
        "chart_type": chart_payload["chart_type"] if chart_payload else None,
        "chart_data": chart_payload["data"] if chart_payload else None,
        "explanation": chart_payload["explanation"] if chart_payload else None,
        "scenario_id": chart_payload.get("scenario_id") if chart_payload else None,
        "title": chart_payload.get("title") if chart_payload else None,
    }


async def ask(question: str, session: AsyncSession) -> dict[str, Any]:
    """Non-streaming answer: consume ask_stream and return the final payload."""
    payload: dict[str, Any] | None = None
    async for event in ask_stream(question, session):
        if event["type"] == "done":
            payload = {k: v for k, v in event.items() if k != "type"}
        elif event["type"] == "error":
            raise RuntimeError(event["detail"])
    if payload is None:
        raise RuntimeError("orchestrator produced no result")
    return payload
