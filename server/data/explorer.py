import asyncio
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings

CSV_PATH = Path(__file__).parent / "logistics_data.csv"
SEP = "=" * 72
SUBSEP = "-" * 72

# Canonical catalog: (group, id, question, chart). Source of truth for the
# 33-scenario registry. Recommendations render 1:1 against this list.
CATALOG: list[tuple[str, str, str, str]] = [
    # Reliability & performance
    ("Reliability", "delay_rate_by_carrier", "Which carrier has the highest delay rate?", "bar"),
    ("Reliability", "delay_rate_by_region", "Which region has the worst delivery performance?", "bar"),
    ("Reliability", "warehouse_performance", "Which warehouse has the worst delay rate?", "bar"),
    ("Reliability", "on_time_trend", "Is delivery performance improving over the year?", "line"),
    ("Reliability", "delivery_time_percentiles", "How long do most orders take? (p50/p90/p95)", "stat"),
    ("Reliability", "exception_deepdive", "Show all exception orders and the carriers they hit", "table"),
    ("Reliability", "delay_rate_by_month", "Which months are worst for delays?", "bar"),
    ("Reliability", "delivery_time_by_month", "Does delivery slow down seasonally?", "line"),
    # Carrier deep-dive
    ("Carrier", "carrier_market_share", "Which carrier handles the most orders?", "pie"),
    ("Carrier", "avg_delivery_time_by_carrier", "Which carrier is fastest / slowest?", "bar"),
    ("Carrier", "revenue_by_carrier", "Which carrier drives the most revenue?", "bar"),
    ("Carrier", "carrier_reliability_trend", "Is each carrier improving or degrading over time?", "multi-line"),
    # Volume & revenue
    ("Volume & revenue", "order_volume_by_month", "Show order volume trend over 2025", "area"),
    ("Volume & revenue", "delivery_performance_by_month", "Delivered vs delayed each month", "stacked bar"),
    ("Volume & revenue", "order_volume_by_region", "Which region orders the most?", "bar"),
    ("Volume & revenue", "revenue_by_region", "Revenue by region", "bar"),
    ("Volume & revenue", "revenue_by_category", "Which category drives most revenue?", "bar"),
    ("Volume & revenue", "top_clients", "Who are our top clients by orders?", "bar"),
    ("Volume & revenue", "revenue_pareto", "What share of revenue comes from top clients?", "stat"),
    ("Volume & revenue", "busiest_routes", "What are our busiest shipping lanes?", "bar"),
    # Routes & delivery
    ("Routes & delivery", "slowest_routes", "Which routes take the longest?", "bar"),
    ("Routes & delivery", "delivery_time_distribution", "How is delivery time distributed?", "histogram"),
    # Category & product
    ("Category & product", "avg_order_value_by_category", "Which category has the highest avg order value?", "bar"),
    ("Category & product", "top_skus", "What are our most-ordered SKUs?", "bar"),
    ("Category & product", "quantity_distribution", "What is the typical order size?", "histogram"),
    ("Category & product", "sku_concentration", "How concentrated is our SKU catalog?", "stat"),
    ("Category & product", "category_x_region", "Where does each category sell? (crosstab)", "heatmap"),
    # Operations & status
    ("Operations & status", "status_distribution", "Order status breakdown", "donut"),
    ("Operations & status", "day_of_week_pattern", "Which days get the most orders?", "bar"),
    ("Operations & status", "order_value_distribution", "How are order values distributed?", "histogram"),
    ("Operations & status", "promo_vs_nonpromo", "Do promo orders delay more than non-promo?", "bar"),
    ("Operations & status", "delivery_time_by_region", "Delivery speed by region", "bar"),
    # Forecast
    ("Forecast", "forecast_demand", "Predict demand for a category for the next N months", "line"),
]


def section(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}")


def sub(title: str) -> None:
    print(f"\n{SUBSEP}\n{title}\n{SUBSEP}")


def print_table(headers: list[str], rows: list[tuple]) -> None:
    widths = [
        max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows else len(str(h))
        for i, h in enumerate(headers)
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))


def money(v) -> str:
    return f"${v:,.2f}" if v is not None else "-"


def pct(num: int, den: int) -> str:
    return f"{100.0 * num / den:.1f}%" if den else "-"


async def dataset_profile(s) -> None:
    section("1. DATASET PROFILE")
    r = (
        await s.execute(
            text(
                "SELECT COUNT(*) AS total, "
                "MIN(order_date) AS min_date, MAX(order_date) AS max_date, "
                "SUM(order_value_usd) AS revenue, AVG(order_value_usd) AS avg_value "
                "FROM orders"
            )
        )
    ).one()
    avg_days = (
        await s.execute(
            text("SELECT AVG(delivery_date - order_date) AS d FROM orders WHERE delivery_date IS NOT NULL")
        )
    ).scalar()
    print(f"Date range:       {r.min_date} -> {r.max_date}")
    print(f"Total orders:     {r.total}")
    print(f"Total revenue:    {money(r.revenue)}")
    print(f"Avg order value:  {money(r.avg_value)}")
    print(f"Avg delivery:     {float(avg_days):.1f} days (n=completed)")


async def dimensions(s) -> None:
    section("2. DIMENSIONS")
    cols = ["carrier", "status", "product_category", "region", "warehouse", "client_id", "sku"]
    out = []
    for c in cols:
        vals = (
            await s.execute(text(f"SELECT {c} AS v, COUNT(*) AS n FROM orders GROUP BY {c} ORDER BY n DESC"))
        ).all()
        sample = ", ".join(v.v for v in vals[:6]) + ("..." if len(vals) > 6 else "")
        out.append((c, len(vals), sample))
    print_table(["dimension", "cardinality", "top values (by count)"], out)


async def kpi_verification(s) -> None:
    section("3. KPI VERIFICATION (dashboard ground truth)")
    r = (
        await s.execute(
            text(
                "SELECT "
                "COUNT(*) AS total, "
                "COUNT(*) FILTER (WHERE status='delivered') AS delivered, "
                "COUNT(*) FILTER (WHERE status='delayed') AS delayed, "
                "AVG(delivery_date - order_date) FILTER (WHERE delivery_date IS NOT NULL) AS avg_days "
                "FROM orders"
            )
        )
    ).one()
    completed = r.delivered + r.delayed
    on_time = 100.0 * r.delivered / completed if completed else 0.0
    print(f"Total orders:      {r.total}")
    print(f"Delivered:         {r.delivered}")
    print(f"Delayed:           {r.delayed}")
    print(f"On-time rate:      {on_time:.1f}%  (delivered / (delivered + delayed))")
    print(f"Avg delivery time: {float(r.avg_days):.1f} days (n={completed} completed)")


async def _delay_rate_by(s, col: str, title: str) -> list:
    sub(title)
    rows = (
        await s.execute(
            text(
                f"SELECT {col} AS dim, "
                "COUNT(*) FILTER (WHERE status IN ('delivered','delayed')) AS completed, "
                "COUNT(*) FILTER (WHERE status='delayed') AS delayed "
                f"FROM orders GROUP BY {col} ORDER BY "
                "100.0 * COUNT(*) FILTER (WHERE status='delayed') / "
                "NULLIF(COUNT(*) FILTER (WHERE status IN ('delivered','delayed')), 0) DESC"
            )
        )
    ).all()
    out = []
    for r in rows:
        rate = 100.0 * r.delayed / r.completed if r.completed else 0.0
        out.append((r.dim, r.completed, r.delayed, f"{rate:.1f}%"))
    print_table([col, "completed", "delayed", "delay_rate"], out)
    return out


async def candidate_scenarios(s) -> dict:
    section("4. ANALYTICS SCENARIOS (32)")
    f: dict = {}

    # ---- Reliability & performance ----
    f["delay_rate_by_carrier"] = await _delay_rate_by(s, "carrier", "delay_rate_by_carrier — Delay rate by carrier")
    if f["delay_rate_by_carrier"]:
        w = f["delay_rate_by_carrier"][0]
        f["worst_carrier"] = f"{w[0]} at {w[3]} ({w[2]} delayed / {w[1]} completed)"

    f["delay_rate_by_region"] = await _delay_rate_by(s, "region", "delay_rate_by_region — Delay rate by region")
    if f["delay_rate_by_region"]:
        w = f["delay_rate_by_region"][0]
        f["worst_region"] = f"{w[0]} at {w[3]} delay rate"

    # warehouse_performance
    sub("warehouse_performance — Warehouse delay rate")
    rows = (
        await s.execute(
            text(
                "SELECT warehouse AS w, COUNT(*) AS orders, "
                "COUNT(*) FILTER (WHERE status='delayed') AS delayed "
                "FROM orders GROUP BY w ORDER BY "
                "100.0 * COUNT(*) FILTER (WHERE status='delayed') / NULLIF(COUNT(*), 0) DESC"
            )
        )
    ).all()
    out = [(r.w, r.orders, r.delayed, pct(r.delayed, r.orders)) for r in rows]
    print_table(["warehouse", "orders", "delayed", "delay_rate"], out)
    if out:
        f["worst_warehouse"] = f"{out[0][0]} at {out[0][3]} delay rate across {out[0][1]} orders"

    # on_time_trend
    sub("on_time_trend — On-time rate by month")
    rows = (
        await s.execute(
            text(
                "SELECT TO_CHAR(order_date,'YYYY-MM') AS m, "
                "COUNT(*) FILTER (WHERE status='delivered') AS delivered, "
                "COUNT(*) FILTER (WHERE status='delayed') AS delayed "
                "FROM orders GROUP BY m ORDER BY m"
            )
        )
    ).all()
    rates = []
    out = []
    for r in rows:
        comp = r.delivered + r.delayed
        rate = 100.0 * r.delivered / comp if comp else 0.0
        rates.append(rate)
        out.append((r.m, comp, f"{rate:.1f}%"))
    print_table(["month", "completed", "on_time_rate"], out)
    if len(rates) >= 6:
        q1, q4 = sum(rates[:3]) / 3, sum(rates[-3:]) / 3
        direction = "improving" if q4 > q1 else "degrading"
        f["on_time_direction"] = f"{direction} Q1 ({q1:.1f}%) -> Q4 ({q4:.1f}%)"

    # delivery_time_percentiles
    sub("delivery_time_percentiles — Delivery time distribution")
    r = (
        await s.execute(
            text(
                "SELECT MIN(delivery_date - order_date) AS min_d, "
                "MAX(delivery_date - order_date) AS max_d, "
                "ROUND(AVG(delivery_date - order_date),1) AS avg_d, "
                "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delivery_date - order_date) AS p50, "
                "PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY delivery_date - order_date) AS p90, "
                "PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY delivery_date - order_date) AS p95 "
                "FROM orders WHERE delivery_date IS NOT NULL"
            )
        )
    ).one()
    print_table(["min", "p50", "avg", "p90", "p95", "max"], [(r.min_d, r.p50, r.avg_d, r.p90, r.p95, r.max_d)])
    f["p90_delivery"] = f"p50={r.p50}d, p90={r.p90}d, p95={r.p95}d, max={r.max_d}d"

    # exception_deepdive
    sub("exception_deepdive — Exception orders by carrier")
    rows = (
        await s.execute(
            text("SELECT carrier AS c, COUNT(*) AS n FROM orders WHERE status='exception' GROUP BY c ORDER BY n DESC")
        )
    ).all()
    if rows:
        print_table(["carrier (exceptions)", "count"], [(r.c, r.n) for r in rows])
        f["exception_deepdive"] = f"{len(rows)} carriers affected, top: {rows[0].c} ({rows[0].n})"
    else:
        print("(no exception orders)")
        f["exception_deepdive"] = "no exception orders"

    # delay_rate_by_month
    sub("delay_rate_by_month — Delay rate by month")
    rows = (
        await s.execute(
            text(
                "SELECT TO_CHAR(order_date,'YYYY-MM') AS m, "
                "COUNT(*) FILTER (WHERE status IN ('delivered','delayed')) AS completed, "
                "COUNT(*) FILTER (WHERE status='delayed') AS delayed "
                "FROM orders GROUP BY m ORDER BY m"
            )
        )
    ).all()
    out = []
    worst_month = None
    for r in rows:
        rate = 100.0 * r.delayed / r.completed if r.completed else 0.0
        out.append((r.m, r.completed, r.delayed, f"{rate:.1f}%"))
        if worst_month is None or rate > worst_month[1]:
            worst_month = (r.m, rate)
    print_table(["month", "completed", "delayed", "delay_rate"], out)
    if worst_month:
        f["worst_delay_month"] = f"{worst_month[0]} at {worst_month[1]:.1f}% delay rate"

    # delivery_time_by_month
    sub("delivery_time_by_month — Avg delivery time by month")
    rows = (
        await s.execute(
            text(
                "SELECT TO_CHAR(order_date,'YYYY-MM') AS m, "
                "ROUND(AVG(delivery_date - order_date),1) AS avg_days "
                "FROM orders WHERE delivery_date IS NOT NULL GROUP BY m ORDER BY m"
            )
        )
    ).all()
    print_table(["month", "avg_days"], [(r.m, r.avg_days) for r in rows])
    if rows:
        slow = max(rows, key=lambda x: float(x.avg_days))
        fast = min(rows, key=lambda x: float(x.avg_days))
        f["slowest_delivery_month"] = f"slowest {slow.m} ({slow.avg_days}d), fastest {fast.m} ({fast.avg_days}d)"

    # ---- Carrier deep-dive ----
    # carrier_market_share
    sub("carrier_market_share — Orders by carrier")
    rows = (await s.execute(text("SELECT carrier AS c, COUNT(*) AS n FROM orders GROUP BY c ORDER BY n DESC"))).all()
    total = sum(r.n for r in rows)
    print_table(["carrier", "orders", "share"], [(r.c, r.n, pct(r.n, total)) for r in rows])
    if rows:
        f["top_carrier_share"] = f"{rows[0].c} handles {pct(rows[0].n, total)} of orders"

    # avg_delivery_time_by_carrier
    sub("avg_delivery_time_by_carrier — Avg delivery time by carrier")
    rows = (
        await s.execute(
            text(
                "SELECT carrier AS c, ROUND(AVG(delivery_date - order_date),1) AS avg_days, "
                "MIN(delivery_date - order_date) AS min_days, MAX(delivery_date - order_date) AS max_days "
                "FROM orders WHERE delivery_date IS NOT NULL GROUP BY c ORDER BY avg_days"
            )
        )
    ).all()
    print_table(["carrier", "avg_days", "min", "max"], [(r.c, r.avg_days, r.min_days, r.max_days) for r in rows])
    if rows:
        f["carrier_speed"] = f"fastest {rows[0].c} ({rows[0].avg_days}d), slowest {rows[-1].c} ({rows[-1].avg_days}d)"

    # revenue_by_carrier
    sub("revenue_by_carrier — Revenue by carrier")
    rows = (
        await s.execute(
            text("SELECT carrier AS c, SUM(order_value_usd) AS rev FROM orders GROUP BY c ORDER BY rev DESC")
        )
    ).all()
    print_table(["carrier", "revenue"], [(r.c, money(r.rev)) for r in rows])
    if rows:
        f["top_revenue_carrier"] = f"{rows[0].c} at {money(rows[0].rev)}"

    # carrier_reliability_trend (H1 vs H2 delay rate per carrier)
    sub("carrier_reliability_trend — Per-carrier delay rate H1 vs H2")
    rows = (
        await s.execute(
            text(
                "SELECT carrier AS c, "
                "COUNT(*) FILTER (WHERE status='delayed' AND order_date < '2025-07-01') AS h1_d, "
                "COUNT(*) FILTER (WHERE status IN ('delivered','delayed') AND order_date < '2025-07-01') AS h1_c, "
                "COUNT(*) FILTER (WHERE status='delayed' AND order_date >= '2025-07-01') AS h2_d, "
                "COUNT(*) FILTER (WHERE status IN ('delivered','delayed') AND order_date >= '2025-07-01') AS h2_c "
                "FROM orders GROUP BY c ORDER BY c"
            )
        )
    ).all()
    out = []
    improving = 0
    degrading = 0
    for r in rows:
        h1 = 100.0 * r.h1_d / r.h1_c if r.h1_c else 0.0
        h2 = 100.0 * r.h2_d / r.h2_c if r.h2_c else 0.0
        delta = h2 - h1
        out.append((r.c, f"{h1:.1f}%", f"{h2:.1f}%", f"{delta:+.1f}"))
        if delta < 0:
            improving += 1
        elif delta > 0:
            degrading += 1
    print_table(["carrier", "H1 delay", "H2 delay", "delta"], out)
    f["carrier_trend_summary"] = f"{improving} improving, {degrading} degrading (H1->H2)"

    # ---- Volume & revenue ----
    # order_volume_by_month
    sub("order_volume_by_month — Order volume by month")
    rows = (
        await s.execute(
            text("SELECT TO_CHAR(order_date,'YYYY-MM') AS m, COUNT(*) AS n FROM orders GROUP BY m ORDER BY m")
        )
    ).all()
    monthly = [(r.m, r.n) for r in rows]
    print_table(["month", "orders"], monthly)
    if monthly:
        peak = max(monthly, key=lambda x: x[1])
        trough = min(monthly, key=lambda x: x[1])
        f["volume_peak"] = f"peak {peak[0]} ({peak[1]}), trough {trough[0]} ({trough[1]})"

    # delivery_performance_by_month
    sub("delivery_performance_by_month — Delivered vs delayed by month")
    rows = (
        await s.execute(
            text(
                "SELECT TO_CHAR(order_date,'YYYY-MM') AS m, "
                "COUNT(*) FILTER (WHERE status='delivered') AS delivered, "
                "COUNT(*) FILTER (WHERE status='delayed') AS delayed "
                "FROM orders GROUP BY m ORDER BY m"
            )
        )
    ).all()
    print_table(["month", "delivered", "delayed"], [(r.m, r.delivered, r.delayed) for r in rows])
    if rows:
        pd_month = max(rows, key=lambda x: x.delayed)
        f["peak_delay_month"] = f"most delayed: {pd_month.m} ({pd_month.delayed})"

    # order_volume_by_region
    sub("order_volume_by_region — Orders by region")
    rows = (await s.execute(text("SELECT region AS r, COUNT(*) AS n FROM orders GROUP BY r ORDER BY n DESC"))).all()
    total = sum(r.n for r in rows)
    print_table(["region", "orders", "share"], [(r.r, r.n, pct(r.n, total)) for r in rows])
    if rows:
        f["top_volume_region"] = f"{rows[0].r} with {rows[0].n} orders ({pct(rows[0].n, total)})"

    # revenue_by_region
    sub("revenue_by_region — Revenue by region")
    rows = (
        await s.execute(text("SELECT region AS r, SUM(order_value_usd) AS rev FROM orders GROUP BY r ORDER BY rev DESC"))
    ).all()
    print_table(["region", "revenue"], [(r.r, money(r.rev)) for r in rows])
    if rows:
        f["top_revenue_region"] = f"{rows[0].r} at {money(rows[0].rev)}"

    # revenue_by_category
    sub("revenue_by_category — Revenue/volume by category")
    rows = (
        await s.execute(
            text(
                "SELECT product_category AS cat, COUNT(*) AS n, SUM(order_value_usd) AS rev, "
                "AVG(order_value_usd) AS avg FROM orders GROUP BY cat ORDER BY rev DESC"
            )
        )
    ).all()
    print_table(["category", "orders", "revenue", "avg_value"], [(r.cat, r.n, money(r.rev), money(r.avg)) for r in rows])
    if rows:
        f["top_revenue_category"] = f"{rows[0].cat} at {money(rows[0].rev)}"

    # top_clients
    sub("top_clients — Top 5 clients by orders")
    rows = (
        await s.execute(
            text(
                "SELECT client_id AS cid, COUNT(*) AS n, SUM(order_value_usd) AS rev "
                "FROM orders GROUP BY cid ORDER BY n DESC LIMIT 5"
            )
        )
    ).all()
    print_table(["client", "orders", "revenue"], [(r.cid, r.n, money(r.rev)) for r in rows])
    if rows:
        f["top_client"] = f"{rows[0].cid} ({rows[0].n} orders, {money(rows[0].rev)})"

    # revenue_pareto
    sub("revenue_pareto — Revenue concentration")
    rows = (
        await s.execute(
            text("SELECT client_id AS cid, SUM(order_value_usd) AS rev FROM orders GROUP BY cid ORDER BY rev DESC")
        )
    ).all()
    total_rev = sum(float(r.rev) for r in rows)
    top5 = 100.0 * sum(float(r.rev) for r in rows[:5]) / total_rev if total_rev else 0.0
    top10 = 100.0 * sum(float(r.rev) for r in rows[:10]) / total_rev if total_rev else 0.0
    print_table(["metric", "value"], [("clients", len(rows)), ("top 5 share", f"{top5:.1f}%"), ("top 10 share", f"{top10:.1f}%")])
    f["top5_revenue_share"] = f"top 5 = {top5:.1f}%, top 10 = {top10:.1f}%"

    # busiest_routes
    sub("busiest_routes — Busiest shipping routes")
    rows = (
        await s.execute(
            text(
                "SELECT origin_city || ' -> ' || destination_city AS route, COUNT(*) AS n "
                "FROM orders GROUP BY origin_city, destination_city ORDER BY n DESC LIMIT 8"
            )
        )
    ).all()
    print_table(["route", "orders"], [(r.route, r.n) for r in rows])
    if rows:
        f["top_route"] = f"{rows[0].route} ({rows[0].n} orders)"

    # ---- Routes & delivery ----
    # slowest_routes
    sub("slowest_routes — Slowest routes (avg delivery time)")
    rows = (
        await s.execute(
            text(
                "SELECT origin_city || ' -> ' || destination_city AS route, "
                "ROUND(AVG(delivery_date - order_date),1) AS avg_days, COUNT(*) AS n "
                "FROM orders WHERE delivery_date IS NOT NULL "
                "GROUP BY origin_city, destination_city HAVING COUNT(*) >= 2 "
                "ORDER BY avg_days DESC LIMIT 8"
            )
        )
    ).all()
    print_table(["route", "avg_days", "orders"], [(r.route, r.avg_days, r.n) for r in rows])
    if rows:
        f["slowest_route"] = f"{rows[0].route} at {rows[0].avg_days}d avg"

    # delivery_time_distribution
    sub("delivery_time_distribution — Delivery time histogram")
    rows = (
        await s.execute(
            text(
                "SELECT (delivery_date - order_date) AS days, COUNT(*) AS n "
                "FROM orders WHERE delivery_date IS NOT NULL GROUP BY days ORDER BY days"
            )
        )
    ).all()
    print_table(["days", "orders"], [(r.days, r.n) for r in rows])
    if rows:
        mode = max(rows, key=lambda x: x.n)
        f["mode_delivery_days"] = f"mode = {mode.days}d ({mode.n} orders)"

    # ---- Category & product ----
    # avg_order_value_by_category
    sub("avg_order_value_by_category — Avg order value by category")
    rows = (
        await s.execute(
            text(
                "SELECT product_category AS cat, ROUND(AVG(order_value_usd),2) AS avg_val "
                "FROM orders GROUP BY cat ORDER BY avg_val DESC"
            )
        )
    ).all()
    print_table(["category", "avg_value"], [(r.cat, money(r.avg_val)) for r in rows])
    if rows:
        f["top_aov_category"] = f"{rows[0].cat} at {money(rows[0].avg_val)} avg"

    # top_skus
    sub("top_skus — Most-ordered SKUs")
    rows = (
        await s.execute(
            text(
                "SELECT sku, product_category AS cat, COUNT(*) AS n, SUM(quantity) AS qty "
                "FROM orders GROUP BY sku, cat ORDER BY n DESC LIMIT 8"
            )
        )
    ).all()
    print_table(["sku", "category", "orders", "quantity"], [(r.sku, r.cat, r.n, r.qty) for r in rows])
    if rows:
        f["top_sku"] = f"{rows[0].sku} ({rows[0].n} orders)"

    # quantity_distribution
    sub("quantity_distribution — Units per order")
    rows = (await s.execute(text("SELECT quantity AS q, COUNT(*) AS n FROM orders GROUP BY q ORDER BY q"))).all()
    print_table(["quantity", "orders"], [(r.q, r.n) for r in rows])
    if rows:
        mode = max(rows, key=lambda x: x.n)
        f["mode_quantity"] = f"mode = {mode.q} units/order ({mode.n} orders)"

    # sku_concentration
    sub("sku_concentration — SKU repeat rate")
    rows = (await s.execute(text("SELECT sku, COUNT(*) AS cnt FROM orders GROUP BY sku"))).all()
    total_skus = len(rows)
    repeated = sum(1 for r in rows if r.cnt > 1)
    rate = 100.0 * repeated / total_skus if total_skus else 0.0
    print_table(["metric", "value"], [("distinct SKUs", total_skus), ("repeated SKUs", repeated), ("repeat rate", f"{rate:.1f}%")])
    f["sku_repeat_rate"] = f"{total_skus} distinct SKUs, {rate:.1f}% repeated"

    # category_x_region (crosstab)
    sub("category_x_region — Category x region crosstab (order counts)")
    rows = (
        await s.execute(
            text(
                "SELECT product_category AS cat, region AS r, COUNT(*) AS n "
                "FROM orders GROUP BY cat, r"
            )
        )
    ).all()
    cats = sorted({r.cat for r in rows})
    regions = sorted({r.r for r in rows})
    cell = {(r.cat, r.r): r.n for r in rows}
    matrix = [[c] + [cell.get((c, rg), 0) for rg in regions] for c in cats]
    print_table(["category \\ region"] + regions, [tuple(m) for m in matrix])
    top_cr = max(rows, key=lambda x: x.n)
    f["top_category_region"] = f"{top_cr.cat} x {top_cr.r} ({top_cr.n} orders)"

    # ---- Operations & status ----
    # status_distribution
    sub("status_distribution — Order status breakdown")
    rows = (await s.execute(text("SELECT status, COUNT(*) AS n FROM orders GROUP BY status ORDER BY n DESC"))).all()
    total = sum(r.n for r in rows)
    print_table(["status", "count", "share"], [(r.status, r.n, pct(r.n, total)) for r in rows])
    if rows:
        f["top_status"] = f"{rows[0].status} {pct(rows[0].n, total)}"

    # day_of_week_pattern
    sub("day_of_week_pattern — Orders by day of week")
    dow_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    rows = (
        await s.execute(
            text(
                "SELECT EXTRACT(DOW FROM order_date)::int AS dow, COUNT(*) AS n "
                "FROM orders GROUP BY dow ORDER BY dow"
            )
        )
    ).all()
    out = [(dow_names[r.dow], r.n) for r in rows]
    print_table(["day", "orders"], out)
    if rows:
        busy = max(rows, key=lambda x: x.n)
        f["busiest_dow"] = f"{dow_names[busy.dow]} ({busy.n} orders)"

    # order_value_distribution
    sub("order_value_distribution — Order value buckets")
    rows = (
        await s.execute(
            text(
                "SELECT CASE "
                "WHEN order_value_usd < 20 THEN '<$20' "
                "WHEN order_value_usd < 40 THEN '$20-40' "
                "WHEN order_value_usd < 60 THEN '$40-60' "
                "WHEN order_value_usd < 80 THEN '$60-80' "
                "ELSE '$80+' END AS bucket, "
                "COUNT(*) AS n, MIN(order_value_usd) AS ord "
                "FROM orders GROUP BY bucket ORDER BY ord"
            )
        )
    ).all()
    print_table(["bucket", "orders"], [(r.bucket, r.n) for r in rows])
    if rows:
        big = max(rows, key=lambda x: x.n)
        f["top_value_bucket"] = f"{big.bucket} ({big.n} orders)"

    # promo_vs_nonpromo
    sub("promo_vs_nonpromo — Promo vs non-promo delay")
    rows = (
        await s.execute(
            text(
                "SELECT is_promo AS p, COUNT(*) AS n, "
                "COUNT(*) FILTER (WHERE status='delayed') AS delayed "
                "FROM orders GROUP BY p ORDER BY p"
            )
        )
    ).all()
    out = [(r.p, r.n, r.delayed, pct(r.delayed, r.n)) for r in rows]
    print_table(["is_promo", "orders", "delayed", "delay_rate"], out)
    if len(out) >= 2:
        f["promo_finding"] = f"non-promo {out[0][3]}, promo {out[1][3]} delay rate"

    # delivery_time_by_region
    sub("delivery_time_by_region — Avg delivery time by region")
    rows = (
        await s.execute(
            text(
                "SELECT region AS r, ROUND(AVG(delivery_date - order_date),1) AS avg_days "
                "FROM orders WHERE delivery_date IS NOT NULL GROUP BY r ORDER BY avg_days DESC"
            )
        )
    ).all()
    print_table(["region", "avg_days"], [(r.r, r.avg_days) for r in rows])
    if rows:
        f["slowest_delivery_region"] = f"{rows[0].r} ({rows[0].avg_days}d avg)"

    return f


# ---- Forecast helpers (inline, no new dependency) ----
def _fc_linear(y: list[float], horizon: int) -> list[float]:
    n = len(y)
    x = list(range(n))
    xbar = sum(x) / n
    ybar = sum(y) / n
    denom = sum((xi - xbar) ** 2 for xi in x) or 1
    slope = sum((xi - xbar) * (yi - ybar) for xi, yi in zip(x, y)) / denom
    intercept = ybar - slope * xbar
    return [intercept + slope * (n + i) for i in range(horizon)]


def _fc_ma(y: list[float], horizon: int, window: int = 3) -> list[float]:
    ma = sum(y[-window:]) / window
    return [ma] * horizon


def _fc_es(y: list[float], horizon: int, alpha: float = 0.3) -> list[float]:
    level = y[0]
    for h in y[1:]:
        level = alpha * h + (1 - alpha) * level
    return [level] * horizon


def _fmt_fc(vals: list[float]) -> str:
    return " ".join(f"{max(0.0, v):.0f}" for v in vals)


def forecast_analysis() -> dict:
    section("5. FORECAST ANALYSIS (readiness + 3-method preview)")
    import math

    df = pd.read_csv(CSV_PATH)
    df["month"] = pd.to_datetime(df["order_date"]).dt.to_period("M")
    all_months = pd.period_range("2025-01", "2025-12", freq="M")

    readiness = []
    good: dict[str, list[float]] = {}
    best = None
    for cat in sorted(df["product_category"].unique()):
        series = (
            df[df["product_category"] == cat]
            .groupby("month")["quantity"]
            .sum()
            .reindex(all_months, fill_value=0)
        )
        y = list(series.values.astype(float))
        n = len(y)
        x = list(range(n))
        xbar = sum(x) / n
        ybar = sum(y) / n
        denom = sum((xi - xbar) ** 2 for xi in x) or 1
        slope = sum((xi - xbar) * (yi - ybar) for xi, yi in zip(x, y)) / denom
        mean = sum(y) / n
        std = (sum((v - mean) ** 2 for v in y) / n) ** 0.5
        trend = "up" if slope > 0.1 else ("down" if slope < -0.1 else "flat")
        verdict = "good" if std >= 1.0 and n >= 6 else "sparse"
        readiness.append((cat, round(mean, 1), round(std, 1), trend, verdict, " ".join(str(int(v)) for v in y)))
        if verdict == "good":
            good[cat] = y
            score = abs(slope) + std
            if best is None or score > best[0]:
                best = (score, cat)

    sub("Readiness (monthly quantity by category)")
    print_table(["category", "mean", "std", "trend", "verdict", "history Jan->Dec"], readiness)

    sub(f"3-method forecast preview (horizon=4) — {len(good)} 'good' categories")
    preview = []
    for cat, y in good.items():
        preview.append((cat, _fmt_fc(_fc_linear(y, 4)), _fmt_fc(_fc_ma(y, 4)), _fmt_fc(_fc_es(y, 4))))
    print_table(["category", "linreg", "mvavg3", "expsmooth(a=0.3)"], preview)

    if best:
        y = good[best[1]]
        all_fc = _fc_linear(y, 4) + _fc_ma(y, 4) + _fc_es(y, 4)
        inv = math.ceil(max(all_fc) * 1.2)
        print(f"\n  strongest forecast demo: {best[1]}  ->  stock ~{inv} units/month (peak forecast + 20% safety)")
    return {"best_forecast_category": best[1] if best else None}


async def recommendations(findings: dict, forecast: dict) -> None:
    section("6. SCENARIO CATALOG (33) — 1:1 with recommendations")
    recs = []
    for group, sid, question, chart in CATALOG:
        if sid == "forecast_demand":
            cat = forecast.get("best_forecast_category") or "the top category"
            answer = f"-> best demo: {cat} (clearest trend/variance)"
        else:
            key = {
                "delay_rate_by_carrier": "worst_carrier",
                "delay_rate_by_region": "worst_region",
                "warehouse_performance": "worst_warehouse",
                "on_time_trend": "on_time_direction",
                "delivery_time_percentiles": "p90_delivery",
                "exception_deepdive": "exception_deepdive",
                "delay_rate_by_month": "worst_delay_month",
                "delivery_time_by_month": "slowest_delivery_month",
                "carrier_market_share": "top_carrier_share",
                "avg_delivery_time_by_carrier": "carrier_speed",
                "revenue_by_carrier": "top_revenue_carrier",
                "carrier_reliability_trend": "carrier_trend_summary",
                "order_volume_by_month": "volume_peak",
                "delivery_performance_by_month": "peak_delay_month",
                "order_volume_by_region": "top_volume_region",
                "revenue_by_region": "top_revenue_region",
                "revenue_by_category": "top_revenue_category",
                "top_clients": "top_client",
                "revenue_pareto": "top5_revenue_share",
                "busiest_routes": "top_route",
                "slowest_routes": "slowest_route",
                "delivery_time_distribution": "mode_delivery_days",
                "avg_order_value_by_category": "top_aov_category",
                "top_skus": "top_sku",
                "quantity_distribution": "mode_quantity",
                "sku_concentration": "sku_repeat_rate",
                "category_x_region": "top_category_region",
                "status_distribution": "top_status",
                "day_of_week_pattern": "busiest_dow",
                "order_value_distribution": "top_value_bucket",
                "promo_vs_nonpromo": "promo_finding",
                "delivery_time_by_region": "slowest_delivery_region",
            }.get(sid, sid)
            answer = findings.get(key, "-")
        recs.append((group, sid, question, chart, answer))

    print_table(["group", "scenario_id", "question", "chart", "expected answer"], recs)
    print(f"\n{SEP}\nDone. {len(recs)} scenarios surfaced.\n{SEP}")


async def main() -> None:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        await dataset_profile(s)
        await dimensions(s)
        await kpi_verification(s)
        findings = await candidate_scenarios(s)

    fc = forecast_analysis()

    async with factory() as s:
        await recommendations(findings, fc)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
