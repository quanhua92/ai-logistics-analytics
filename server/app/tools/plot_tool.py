"""Plot tool — render an arbitrary dataset as a chart (passthrough).

The model supplies the data points (from a prior tool result) and a chart type
from a fixed set; we validate, optionally project to the requested x/y fields,
and hand the result to the chart renderer. No DB query, no aggregation — this
visualizes data already retrieved. The model must only plot numbers that came
from a prior tool result, never invented/estimated data.
"""

from __future__ import annotations

from typing import Any

# Fixed set of chart types this tool can render (all x/y-friendly).
_CHART_TYPES = {"bar", "line", "area", "pie", "donut"}


async def plot_data(spec: dict, session: Any = None) -> dict:
    """Render ``data`` as ``chart_type``.

    spec:
        data:       non-empty list of row objects (from a prior tool result)
        chart_type: bar|line|area|pie|donut
        x:          optional category/label field name
        y:          optional value field name (or list of names for multi-series)
    """
    data = spec.get("data")
    chart_type = spec.get("chart_type", "bar")
    x = spec.get("x")
    y = spec.get("y")

    if chart_type not in _CHART_TYPES:
        raise ValueError(f"chart_type must be one of {sorted(_CHART_TYPES)}")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        raise ValueError("data must be a non-empty list of objects")

    y_fields = [y] if isinstance(y, str) else (y or [])

    # Project to the requested x + y field(s) so the renderer gets a clean shape
    # (first key = label/x, remaining keys = value series). If x/y aren't given
    # or don't match, pass the rows through unchanged.
    if x or y_fields:
        projected: list[dict[str, Any]] = []
        for r in data:
            row: dict[str, Any] = {}
            if x:
                row[x] = r.get(x)
            for yf in y_fields:
                if yf not in row:
                    row[yf] = r.get(yf)
            projected.append(row if (x and x in r) or any(yf in r for yf in y_fields) else r)
        rows = projected
    else:
        rows = data

    return {
        "chart_type": chart_type,
        "data": rows,
        "explanation": {
            "metric": "plotted_data",
            "dimensions": [x] if x else [],
            "method": f"data plotted as {chart_type}",
            "data_summary": {"row_count": len(rows)},
        },
    }
