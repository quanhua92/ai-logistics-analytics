"""Explainability metadata builder.

Every analytics response (curated scenario or ad-hoc query) carries an
``explanation`` block describing *what* was measured, *how*, and with which
filters — so the AI answer and the UI can both justify their numbers.
"""

from __future__ import annotations

from typing import Any


def build_explanation(
    *,
    metric: str,
    dimensions: list[str],
    method: str,
    filters: list[dict[str, Any]] | None = None,
    row_count: int | None = None,
) -> dict[str, Any]:
    """Assemble a structured explanation block."""
    explanation: dict[str, Any] = {
        "metric": metric,
        "dimensions": dimensions,
        "method": method,
        "filters_used": filters or [],
    }
    if row_count is not None:
        explanation["data_summary"] = {"row_count": row_count}
    return explanation


def interpretation_text(explanation: dict[str, Any]) -> str:
    """Render a one-line natural-language summary of the query plan."""
    dims = explanation.get("dimensions") or []
    metric = explanation.get("metric", "value")
    parts: list[str] = []
    if dims:
        parts.append(f"grouped by {', '.join(dims)}")
    parts.append(f"measuring {metric}")
    filters = explanation.get("filters_used") or []
    if filters:
        fl = ", ".join(f"{f['field']} {f.get('op', '=')} {f['value']}" for f in filters)
        parts.append(f"filtered to {fl}")
    return "; ".join(parts)
