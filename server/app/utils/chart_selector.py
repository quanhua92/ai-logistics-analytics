"""Rules-based chart-type selection for the open-ended query path.

Curated scenarios declare their own ``chart_type``; this module picks one for
ad-hoc ``query_analytics`` results based on the number of dimensions and the
result shape.
"""

from __future__ import annotations

from typing import Any

# Dimensions that represent a temporal axis.
_TIME_DIMS = {"month", "week", "day_of_week", "dow", "date"}


def pick_chart_type(dimensions: list[str], rows: list[dict[str, Any]]) -> str:
    """Return a Recharts-friendly chart type for the given result shape."""
    dims = [d for d in dimensions]
    n = len(rows)

    # No grouping -> a single aggregate value.
    if not dims:
        return "stat"

    # Time-series (single temporal dimension) -> area/line.
    if len(dims) == 1 and dims[0] in _TIME_DIMS:
        return "area" if n > 1 else "stat"

    # Single categorical dimension -> bar (or donut for small, part-of-whole).
    if len(dims) == 1:
        if n <= 7:
            return "bar"
        return "bar"

    # Two dimensions -> grouped bar (heatmap would need a matrix renderer).
    if len(dims) == 2:
        return "stacked bar"

    return "table"
