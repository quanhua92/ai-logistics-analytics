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

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.scenarios import registry
from app.tools import forecast_tool, orders_tool, query_tool, scenario_tool
from app.utils import chat_log

_MAX_STEPS = 6

_SYSTEM_HEADER = """\
You are the analytics assistant for a logistics company. You answer questions
about orders, deliveries, carriers, regions, products, and revenue using a set
of read-only analytics tools backed by a PostgreSQL database.

The dataset covers shipping orders for all of 2025 (January through December).
So "last month" / "most recent month" means 2025-12; "this year" is 2025.

RULES
1. ALWAYS call a tool before stating any number, ranking, or trend. Never
   fabricate or recall figures from memory.
2. Prefer the curated `run_scenario` tool (fast, pre-validated) over the ad-hoc
   `query_analytics` tool. There is a curated scenario for most common questions.
3. If you are unsure whether a scenario exists or what its parameters are, call
   `list_scenarios` first.
4. After the tool returns, give a concise, plain-English answer. Call out the
   single most important insight, then supporting detail.
5. If the question is ambiguous, ask ONE short clarifying question before
   running any tool.
6. For forecasts, use `forecast_demand` (pure statistics — no guessing).
7. If the user greets you (hi, hello, hey) or asks something outside logistics
   analytics (jokes, general chat, other topics), do NOT call any tool. Reply in
   ONE short, friendly sentence and gently redirect to what you can do (orders,
   carriers, delays, revenue, forecasts). Never refuse flatly.

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
- list_orders(filters, limit): return raw order rows (newest first) when the user
  asks to list/show/recent orders (NOT an aggregate). filters is a dict whose
  keys are carrier|region|status|category|client|sku|warehouse|is_promo|month;
  month is YYYY-MM (e.g. "2025-12"). limit defaults to 20, max 100.
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

    @tool
    async def list_orders(
        filters: dict | None = None,
        limit: int | None = None,
    ) -> dict:
        """Return raw order rows (newest first) for list/show/recent-order queries."""
        return await orders_tool.list_orders({"filters": filters, "limit": limit}, session)

    return [
        list_scenarios,
        run_scenario,
        query_analytics,
        list_orders,
        list_forecast_categories,
        forecast_demand,
    ]


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
    if tool_name == "list_orders":
        return {
            "chart_type": "table",
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


def _history_messages(history: list) -> list:
    """Convert client-sent turns (user/assistant text) into LangChain messages."""
    out: list = []
    for turn in history or []:
        role = getattr(turn, "role", None) or (turn.get("role") if isinstance(turn, dict) else None)
        content = getattr(turn, "content", None) or (turn.get("content") if isinstance(turn, dict) else "")
        if not content:
            continue
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
    return out


async def ask_stream(
    question: str,
    session: AsyncSession,
    history: list | None = None,
    conversation_id: str = "",
):
    """Async generator yielding SSE event dicts.

    Events: status, tool, token, done, error. The ``done`` event carries the
    same payload shape as :func:`ask` so streaming and non-streaming clients
    render identically. ``history`` is the prior user/assistant text turns.
    Each completed turn is appended to the conversation's JSONL log.
    """
    if not settings.openrouter_api_key:
        yield {"type": "error", "detail": "OPENROUTER_API_KEY is not set — add it to server/.env"}
        return

    llm = _make_llm()
    tools = _make_tools(session)
    tool_map = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    messages: list = [SystemMessage(content=build_system_prompt())]
    messages.extend(_history_messages(history))
    messages.append(HumanMessage(content=question))
    chart_payload: dict | None = None
    acc = None
    tool_log: list[dict[str, Any]] = []

    def _log_turn(answer: str = "", error: str | None = None) -> None:
        chat_log.append_turn(
            conversation_id,
            {
                "question": question,
                "history_len": len(history or []),
                "tool_calls": tool_log,
                "answer": answer,
                "chart_type": chart_payload["chart_type"] if chart_payload else None,
                "scenario_id": chart_payload.get("scenario_id") if chart_payload else None,
                "error": error,
            },
        )

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
                status = "ok"
                try:
                    result = await tool_map[name].ainvoke(args)
                except Exception as exc:  # surface tool errors to the model so it can recover
                    result = {"error": f"{type(exc).__name__}: {exc}"}
                    status = f"{type(exc).__name__}: {exc}"
                tool_log.append({"name": name, "args": args, "status": status})
                captured = _capture_chart(name, result)
                if captured:
                    chart_payload = captured
                messages.append(
                    ToolMessage(content=json.dumps(result, default=str), tool_call_id=call_id)
                )
    except Exception as exc:
        _log_turn(error=f"{type(exc).__name__}: {exc}")
        yield {"type": "error", "detail": f"{type(exc).__name__}: {exc}"}
        return

    answer = (acc.content if acc and acc.content else "").strip() or "(no answer)"
    _log_turn(answer=answer)
    yield {
        "type": "done",
        "answer": answer,
        "chart_type": chart_payload["chart_type"] if chart_payload else None,
        "chart_data": chart_payload["data"] if chart_payload else None,
        "explanation": chart_payload["explanation"] if chart_payload else None,
        "scenario_id": chart_payload.get("scenario_id") if chart_payload else None,
        "title": chart_payload.get("title") if chart_payload else None,
    }


async def ask(
    question: str,
    session: AsyncSession,
    history: list | None = None,
    conversation_id: str = "",
) -> dict[str, Any]:
    """Non-streaming answer: consume ask_stream and return the final payload."""
    payload: dict[str, Any] | None = None
    async for event in ask_stream(question, session, history=history, conversation_id=conversation_id):
        if event["type"] == "done":
            payload = {k: v for k, v in event.items() if k != "type"}
        elif event["type"] == "error":
            raise RuntimeError(event["detail"])
    if payload is None:
        raise RuntimeError("orchestrator produced no result")
    return payload
