from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Scenario:
    id: str
    group: str
    title: str
    question: str
    chart_type: str
    sql: str
    explanation: dict[str, Any] = field(default_factory=dict)


def _scn(
    id: str,
    group: str,
    title: str,
    question: str,
    chart_type: str,
    sql: str,
    metric: str,
    dimensions: list[str],
    method: str,
) -> Scenario:
    return Scenario(
        id=id,
        group=group,
        title=title,
        question=question,
        chart_type=chart_type,
        sql=sql.strip(),
        explanation={"metric": metric, "dimensions": dimensions, "method": method},
    )


_DELAY_RATE_FILTER = (
    "COUNT(*) FILTER (WHERE status IN ('delivered','delayed')) AS completed, "
    "COUNT(*) FILTER (WHERE status='delayed') AS delayed, "
    "ROUND(100.0 * COUNT(*) FILTER (WHERE status='delayed') / "
    "NULLIF(COUNT(*) FILTER (WHERE status IN ('delivered','delayed')), 0), 1) AS delay_rate"
)

_SCENARIOS: list[Scenario] = [
    # ──────────────────────────────────────────────────────────────
    # Reliability & performance
    # ──────────────────────────────────────────────────────────────
    _scn(
        "delay_rate_by_carrier", "Reliability & performance",
        "Delay rate by carrier", "Which carrier has the highest delay rate?", "bar",
        f"SELECT carrier, {_DELAY_RATE_FILTER} FROM orders GROUP BY carrier ORDER BY delay_rate DESC",
        "delay_rate", ["carrier"], "delayed / (delivered + delayed) × 100",
    ),
    _scn(
        "delay_rate_by_region", "Reliability & performance",
        "Delay rate by region", "Which region has the worst delivery performance?", "bar",
        f"SELECT region, {_DELAY_RATE_FILTER} FROM orders GROUP BY region ORDER BY delay_rate DESC",
        "delay_rate", ["region"], "delayed / (delivered + delayed) × 100",
    ),
    _scn(
        "warehouse_performance", "Reliability & performance",
        "Warehouse performance", "Which warehouse has the worst delay rate?", "bar",
        "SELECT warehouse, COUNT(*) AS orders, "
        "COUNT(*) FILTER (WHERE status='delayed') AS delayed, "
        "ROUND(100.0 * COUNT(*) FILTER (WHERE status='delayed') / NULLIF(COUNT(*), 0), 1) AS delay_rate "
        "FROM orders GROUP BY warehouse ORDER BY delay_rate DESC",
        "delay_rate", ["warehouse"], "delayed / total orders × 100",
    ),
    _scn(
        "on_time_trend", "Reliability & performance",
        "On-time rate trend", "Is delivery performance improving over the year?", "line",
        "SELECT TO_CHAR(order_date,'YYYY-MM') AS month, "
        "COUNT(*) FILTER (WHERE status='delivered') AS delivered, "
        "COUNT(*) FILTER (WHERE status='delayed') AS delayed, "
        "ROUND(100.0 * COUNT(*) FILTER (WHERE status='delivered') / "
        "NULLIF(COUNT(*) FILTER (WHERE status IN ('delivered','delayed')), 0), 1) AS on_time_rate "
        "FROM orders GROUP BY month ORDER BY month",
        "on_time_rate", ["month"], "delivered / (delivered + delayed) × 100 per month",
    ),
    _scn(
        "delivery_time_percentiles", "Reliability & performance",
        "Delivery time percentiles", "How long do most orders take? (p50/p90/p95)", "stat",
        "SELECT MIN(delivery_date - order_date) AS min_days, "
        "MAX(delivery_date - order_date) AS max_days, "
        "ROUND(AVG(delivery_date - order_date), 1) AS avg_days, "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delivery_date - order_date) AS p50, "
        "PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY delivery_date - order_date) AS p90, "
        "PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY delivery_date - order_date) AS p95 "
        "FROM orders WHERE delivery_date IS NOT NULL",
        "delivery_time_days", [], "percentiles of (delivery_date - order_date)",
    ),
    _scn(
        "exception_deepdive", "Reliability & performance",
        "Exception orders deep-dive", "Show all exception orders and the carriers they hit", "table",
        "SELECT carrier, COUNT(*) AS orders "
        "FROM orders WHERE status='exception' GROUP BY carrier ORDER BY orders DESC",
        "exception_count", ["carrier"], "count of status='exception' grouped by carrier",
    ),
    _scn(
        "delay_rate_by_month", "Reliability & performance",
        "Delay rate by month", "Which months are worst for delays?", "bar",
        "SELECT TO_CHAR(order_date,'YYYY-MM') AS month, "
        + _DELAY_RATE_FILTER
        + " FROM orders GROUP BY month ORDER BY month",
        "delay_rate", ["month"], "delayed / (delivered + delayed) × 100 per month",
    ),
    _scn(
        "delivery_time_by_month", "Reliability & performance",
        "Avg delivery time by month", "Does delivery slow down seasonally?", "line",
        "SELECT TO_CHAR(order_date,'YYYY-MM') AS month, "
        "ROUND(AVG(delivery_date - order_date), 1) AS avg_days, "
        "COUNT(*) AS orders "
        "FROM orders WHERE delivery_date IS NOT NULL GROUP BY month ORDER BY month",
        "delivery_time_days", ["month"], "avg(delivery_date - order_date) per month",
    ),
    # ──────────────────────────────────────────────────────────────
    # Carrier deep-dive
    # ──────────────────────────────────────────────────────────────
    _scn(
        "carrier_market_share", "Carrier deep-dive",
        "Carrier market share", "Which carrier handles the most orders?", "pie",
        "SELECT carrier, COUNT(*) AS orders, "
        "ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share "
        "FROM orders GROUP BY carrier ORDER BY orders DESC",
        "order_count", ["carrier"], "count and share of orders per carrier",
    ),
    _scn(
        "avg_delivery_time_by_carrier", "Carrier deep-dive",
        "Avg delivery time by carrier", "Which carrier is fastest / slowest?", "bar",
        "SELECT carrier, ROUND(AVG(delivery_date - order_date), 1) AS avg_days, "
        "MIN(delivery_date - order_date) AS min_days, "
        "MAX(delivery_date - order_date) AS max_days, COUNT(*) AS orders "
        "FROM orders WHERE delivery_date IS NOT NULL GROUP BY carrier ORDER BY avg_days",
        "delivery_time_days", ["carrier"], "avg(min/max) of delivery days per carrier",
    ),
    _scn(
        "revenue_by_carrier", "Carrier deep-dive",
        "Revenue by carrier", "Which carrier drives the most revenue?", "bar",
        "SELECT carrier, SUM(order_value_usd) AS revenue, COUNT(*) AS orders "
        "FROM orders GROUP BY carrier ORDER BY revenue DESC",
        "revenue", ["carrier"], "sum(order_value_usd) per carrier",
    ),
    _scn(
        "carrier_reliability_trend", "Carrier deep-dive",
        "Carrier reliability trend", "Is each carrier improving or degrading over time?", "multi-line",
        "SELECT carrier, "
        "ROUND(100.0 * COUNT(*) FILTER (WHERE status='delayed' AND order_date < '2025-07-01') / "
        "NULLIF(COUNT(*) FILTER (WHERE status IN ('delivered','delayed') AND order_date < '2025-07-01'), 0), 1) AS h1_delay_rate, "
        "ROUND(100.0 * COUNT(*) FILTER (WHERE status='delayed' AND order_date >= '2025-07-01') / "
        "NULLIF(COUNT(*) FILTER (WHERE status IN ('delivered','delayed') AND order_date >= '2025-07-01'), 0), 1) AS h2_delay_rate "
        "FROM orders GROUP BY carrier ORDER BY carrier",
        "delay_rate", ["carrier", "half"], "delay rate H1 vs H2 per carrier",
    ),
    # ──────────────────────────────────────────────────────────────
    # Volume & revenue
    # ──────────────────────────────────────────────────────────────
    _scn(
        "order_volume_by_month", "Volume & revenue",
        "Order volume by month", "Show order volume trend over 2025", "area",
        "SELECT TO_CHAR(order_date,'YYYY-MM') AS month, COUNT(*) AS orders "
        "FROM orders GROUP BY month ORDER BY month",
        "order_count", ["month"], "count of orders per month",
    ),
    _scn(
        "delivery_performance_by_month", "Volume & revenue",
        "Delivery performance by month", "Delivered vs delayed each month", "stacked bar",
        "SELECT TO_CHAR(order_date,'YYYY-MM') AS month, "
        "COUNT(*) FILTER (WHERE status='delivered') AS delivered, "
        "COUNT(*) FILTER (WHERE status='delayed') AS delayed "
        "FROM orders GROUP BY month ORDER BY month",
        "order_count", ["month", "status"], "delivered vs delayed counts per month",
    ),
    _scn(
        "order_volume_by_region", "Volume & revenue",
        "Order volume by region", "Which region orders the most?", "bar",
        "SELECT region, COUNT(*) AS orders, "
        "ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share "
        "FROM orders GROUP BY region ORDER BY orders DESC",
        "order_count", ["region"], "count and share of orders per region",
    ),
    _scn(
        "revenue_by_region", "Volume & revenue",
        "Revenue by region", "Revenue by region", "bar",
        "SELECT region, SUM(order_value_usd) AS revenue, COUNT(*) AS orders "
        "FROM orders GROUP BY region ORDER BY revenue DESC",
        "revenue", ["region"], "sum(order_value_usd) per region",
    ),
    _scn(
        "revenue_by_category", "Volume & revenue",
        "Revenue by category", "Which category drives most revenue?", "bar",
        "SELECT product_category AS category, COUNT(*) AS orders, "
        "SUM(order_value_usd) AS revenue, AVG(order_value_usd) AS avg_value "
        "FROM orders GROUP BY category ORDER BY revenue DESC",
        "revenue", ["category"], "sum/avg(order_value_usd) per category",
    ),
    _scn(
        "top_clients", "Volume & revenue",
        "Top clients", "Who are our top clients by orders?", "bar",
        "SELECT client_id, COUNT(*) AS orders, SUM(order_value_usd) AS revenue "
        "FROM orders GROUP BY client_id ORDER BY orders DESC LIMIT 10",
        "order_count", ["client"], "top 10 clients by order count",
    ),
    _scn(
        "revenue_pareto", "Volume & revenue",
        "Revenue Pareto", "What share of revenue comes from top clients?", "stat",
        "SELECT client_id, SUM(order_value_usd) AS revenue "
        "FROM orders GROUP BY client_id ORDER BY revenue DESC",
        "revenue", ["client"], "per-client revenue (sorted) for Pareto curve",
    ),
    _scn(
        "busiest_routes", "Volume & revenue",
        "Busiest routes", "What are our busiest shipping lanes?", "bar",
        "SELECT origin_city || ' -> ' || destination_city AS route, COUNT(*) AS orders "
        "FROM orders GROUP BY origin_city, destination_city ORDER BY orders DESC LIMIT 10",
        "order_count", ["route"], "top 10 origin→destination pairs by order count",
    ),
    # ──────────────────────────────────────────────────────────────
    # Routes & delivery
    # ──────────────────────────────────────────────────────────────
    _scn(
        "slowest_routes", "Routes & delivery",
        "Slowest routes", "Which routes take the longest?", "bar",
        "SELECT origin_city || ' -> ' || destination_city AS route, "
        "ROUND(AVG(delivery_date - order_date), 1) AS avg_days, COUNT(*) AS orders "
        "FROM orders WHERE delivery_date IS NOT NULL "
        "GROUP BY origin_city, destination_city HAVING COUNT(*) >= 2 "
        "ORDER BY avg_days DESC LIMIT 10",
        "delivery_time_days", ["route"], "avg delivery days per route (min 2 orders)",
    ),
    _scn(
        "delivery_time_distribution", "Routes & delivery",
        "Delivery time distribution", "How is delivery time distributed?", "histogram",
        "SELECT (delivery_date - order_date) AS days, COUNT(*) AS orders "
        "FROM orders WHERE delivery_date IS NOT NULL GROUP BY days ORDER BY days",
        "order_count", ["delivery_time_days"], "histogram of delivery days",
    ),
    # ──────────────────────────────────────────────────────────────
    # Category & product
    # ──────────────────────────────────────────────────────────────
    _scn(
        "avg_order_value_by_category", "Category & product",
        "Avg order value by category", "Which category has the highest avg order value?", "bar",
        "SELECT product_category AS category, ROUND(AVG(order_value_usd), 2) AS avg_value, COUNT(*) AS orders "
        "FROM orders GROUP BY category ORDER BY avg_value DESC",
        "avg_order_value", ["category"], "avg(order_value_usd) per category",
    ),
    _scn(
        "top_skus", "Category & product",
        "Top SKUs", "What are our most-ordered SKUs?", "bar",
        "SELECT sku, product_category AS category, COUNT(*) AS orders, SUM(quantity) AS quantity "
        "FROM orders GROUP BY sku, category ORDER BY orders DESC LIMIT 10",
        "order_count", ["sku"], "top 10 SKUs by order count",
    ),
    _scn(
        "quantity_distribution", "Category & product",
        "Quantity distribution", "What is the typical order size?", "histogram",
        "SELECT quantity, COUNT(*) AS orders FROM orders GROUP BY quantity ORDER BY quantity",
        "order_count", ["quantity"], "histogram of units per order",
    ),
    _scn(
        "sku_concentration", "Category & product",
        "SKU concentration", "How concentrated is our SKU catalog?", "stat",
        "SELECT COUNT(*) AS distinct_skus, "
        "SUM(CASE WHEN cnt > 1 THEN 1 ELSE 0 END) AS repeated_skus, "
        "ROUND(100.0 * SUM(CASE WHEN cnt > 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_rate "
        "FROM (SELECT sku, COUNT(*) AS cnt FROM orders GROUP BY sku) t",
        "sku_count", [], "distinct SKUs, repeated count, repeat rate",
    ),
    _scn(
        "category_x_region", "Category & product",
        "Category × region", "Where does each category sell? (crosstab)", "heatmap",
        "SELECT product_category AS category, region, COUNT(*) AS orders "
        "FROM orders GROUP BY category, region ORDER BY category, region",
        "order_count", ["category", "region"], "order counts per category × region (long form)",
    ),
    # ──────────────────────────────────────────────────────────────
    # Operations & status
    # ──────────────────────────────────────────────────────────────
    _scn(
        "status_distribution", "Operations & status",
        "Status distribution", "Order status breakdown", "donut",
        "SELECT status, COUNT(*) AS orders, "
        "ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share "
        "FROM orders GROUP BY status ORDER BY orders DESC",
        "order_count", ["status"], "count and share of each status",
    ),
    _scn(
        "day_of_week_pattern", "Operations & status",
        "Day of week pattern", "Which days get the most orders?", "bar",
        "SELECT EXTRACT(DOW FROM order_date)::int AS dow, COUNT(*) AS orders "
        "FROM orders GROUP BY dow ORDER BY dow",
        "order_count", ["day_of_week"], "orders per day of week (0=Sun..6=Sat)",
    ),
    _scn(
        "order_value_distribution", "Operations & status",
        "Order value distribution", "How are order values distributed?", "histogram",
        "SELECT CASE WHEN order_value_usd < 20 THEN '<$20' "
        "WHEN order_value_usd < 40 THEN '$20-40' "
        "WHEN order_value_usd < 60 THEN '$40-60' "
        "WHEN order_value_usd < 80 THEN '$60-80' "
        "ELSE '$80+' END AS bucket, COUNT(*) AS orders, MIN(order_value_usd) AS sort_key "
        "FROM orders GROUP BY bucket ORDER BY sort_key",
        "order_count", ["order_value_bucket"], "histogram of order value buckets",
    ),
    _scn(
        "promo_vs_nonpromo", "Operations & status",
        "Promo vs non-promo", "Do promo orders delay more than non-promo?", "bar",
        "SELECT is_promo, COUNT(*) AS orders, "
        "COUNT(*) FILTER (WHERE status='delayed') AS delayed, "
        "ROUND(100.0 * COUNT(*) FILTER (WHERE status='delayed') / NULLIF(COUNT(*), 0), 1) AS delay_rate "
        "FROM orders GROUP BY is_promo ORDER BY is_promo",
        "delay_rate", ["is_promo"], "delay rate promo vs non-promo",
    ),
    _scn(
        "delivery_time_by_region", "Operations & status",
        "Delivery time by region", "Delivery speed by region", "bar",
        "SELECT region, ROUND(AVG(delivery_date - order_date), 1) AS avg_days, COUNT(*) AS orders "
        "FROM orders WHERE delivery_date IS NOT NULL GROUP BY region ORDER BY avg_days DESC",
        "delivery_time_days", ["region"], "avg delivery days per region",
    ),
]

_BY_ID: dict[str, Scenario] = {s.id: s for s in _SCENARIOS}


def all_scenarios() -> list[Scenario]:
    return list(_SCENARIOS)


def get(scenario_id: str) -> Scenario | None:
    return _BY_ID.get(scenario_id)
