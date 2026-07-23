# Logistics AI Analytics Dashboard - Overview & Architecture Guide

## 1. What Is This Project?

This project is an **AI-powered Logistics Analytics Dashboard** - a control center for a shipping company. Imagine a logistics manager who oversees hundreds of shipments across carriers (FedEx, UPS, DHL, etc.) every month. Currently, operational data sits in flat spreadsheets. This application turns that raw logistics data into an **interactive, intelligent web dashboard** that lets people ask questions in plain English and get answers visually.

The app does three things, each progressively smarter:

1. **Descriptive - Show me what happened**
   A dashboard with numbers and charts. "We shipped 400 orders, 55 were late, our on-time rate is 84.7%."

2. **Diagnostic - Help me understand why**
   A chat box where you type questions like "Which carrier has the highest delay rate?" and the system gives you the answer + a chart + an explanation of how it got that answer.

3. **Predictive - Tell me what's coming**
   A forecasting tool where you pick a product category and it predicts how much demand to expect in the next few months, so you can plan inventory.

---

## 2. Data Overview (`mock_logistics_data.csv`)

The dataset is essentially a table of **400 shipping transactions** spanning a full year (Jan 1, 2025 - Dec 30, 2025). Each row is one order.

### Example Row (in plain English)

> Client **CL-1023** placed order **ORD-0001** on **Oct 19, 2025**. It was **2 units** of **PAPER** (SKU `PAPER-0197`) at **$13.11** each, totaling **$26.22**. It shipped from **London** via **DHL** to **Leeds**, out of warehouse **LON-FC1** in the **UK** region. It was delivered on **Oct 22** - that's **3 days**. Status: **delivered**. No promotion.

### Key Dimensions (what you can slice by)

| Dimension         | What it means          | Count & Values                                                              |
| ----------------- | ---------------------- | --------------------------------------------------------------------------- |
| Carrier           | Who shipped it         | 9 - FedEx, UPS, DHL, USPS, OnTrac, LaserShip, Royal Mail, DPD, GLS          |
| Status            | What happened          | 5 - delivered (76%), delayed (13.8%), in_transit (6.8%), exception (2.8%), canceled (0.8%) |
| Product Category  | What was shipped       | 8 - CRAYON, STICKER, MARKER, BRUSH, PAINT, PENCIL, PAPER, BOOK              |
| Region            | Where it went          | 5 - US-E, US-W, US-C, UK, EU                                                |
| Warehouse         | Where it shipped from  | 9 - LON-FC1, EWR-DC1, SFO-DC2, ATL-DC1, LAX-DC1, AMS-FC1, DFW-DC1, BER-FC1, CHI-DC1 |
| Client            | Who ordered it         | 30 clients                                                                  |
| Time              | When                   | 12 months, Jan-Dec 2025                                                     |

### Key Measures (what you can compute)

| Measure          | Example                                                  |
| ---------------- | -------------------------------------------------------- |
| Order count      | 400 total                                                |
| Delivery time    | avg 3.8 days (range: 1-12)                               |
| Delay rate       | 55 delayed out of 359 completed (delivered + delayed) = 15.3% |
| Revenue          | $13,695.87 total, $34.24 avg per order                   |
| Quantity         | Units shipped per order                                  |
| On-time rate     | 84.7% (Delivered / (Delivered + Delayed))                |

---

## 3. User Interface Structure

The web application consists of 3 main pages:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             NAVBAR / SIDEBAR                             │
│   [ Dashboard ]              [ AI Chat ]           [ Forecast ]       │
└──────────────────────────────────────────────────────────────────────────┘
```

### Page 1: Dashboard (`/`)
Designed for immediate operational awareness - the page a logistics manager opens every morning.

**Top row - 5 KPI cards:**

```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Total Orders│ │  Delivered  │ │   Delayed   │ │ On-time Rate│ │ Avg Delivery│
│     400     │ │     304     │ │      55     │ │    84.7%    │ │   3.8 days  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

**Below - 3 charts side by side:**

1. **Order volume over time** - line/area chart showing how many orders per month (e.g., Jan had 75, Sep had 18).
2. **Delivery performance** - stacked bar showing delivered vs delayed each month.
3. **Carrier breakdown** - bar chart comparing each carrier's delay rate (e.g., DHL 5.3% vs UPS 22.4%).

### Page 2: Natural Language AI Interface (`/chat`)
A chat interface - like ChatGPT but for your logistics data.

```
┌──────────────────────────────────────────────┐
│   Ask me anything about your logistics data  │
│                                              │
│ You: "Which carrier has the highest delay    │
│       rate?"                                 │
│                                              │
│ AI:  UPS has the highest delay rate at 22.4% │
│      (17 delayed out of 76 completed orders) │
│                                              │
│      [====== Bar Chart ======]               │
│      UPS:        ████████████ 22.4%          │
│      USPS:       ███████████  23.9%          │
│      Royal Mail: ██████████   20.8%          │
│      ...                                     │
│                                              │
│      ▼ Explanation                           │
│      Filters: none                           │
│      Metric: delay_rate                      │
│      Grouped by: carrier                     │
│      Method: delayed / (delivered + delayed) │
│                                              │
│ You: [Type your question here...]     [Send] │
└──────────────────────────────────────────────┘
```

Every answer includes:
1. **Text answer** - direct human-readable response.
2. **Chart** - dynamically selected (Bar, Line, Pie, Stat Card) when appropriate.
3. **Collapsible Explanation** - applied filters, metrics, dimensions, and the structured query plan.
4. **Toggleable raw data preview**.

### Page 3: Demand Forecasting (`/forecast`)
A simple form + result view for predictive inventory planning.

```
┌────────────────────────────────────────────┐
│ Demand Forecast                            │
│                                            │
│ Product Category: [CRAYON ▼]               │
│ Forecast Horizon: [4 months]               │
│                           [Generate]       │
│                                            │
│ ┌────────────────────────────────────────┐  │
│ │  Historical ── + Forecast - - -         │  │
│ │                                       │  │
│ │  8│         ·                         │  │
│ │  6│  ·  ·  · ·  ·           - - - -  │  │
│ │  4│              · ·  ·  · ·         │  │
│ │  2│                        · - - -   │  │
│ │   └──────────────────────────────────│  │
│ │   J F M A M J J A S O N D J F M A   │  │
│ │         2025              2026       │  │
│ └────────────────────────────────────────┘  │
│                                            │
│ Recommendation: Stock ~18 units/month       │
│ Method: Exponential smoothing               │
└────────────────────────────────────────────┘
```

**Visualization**: Historical monthly demand line + dashed future projection with confidence intervals. **Inventory recommendation**: suggested safety stock & reorder numbers based on the model output.

---

## 4. AI Orchestration & Architecture

### The Core Flow

This is the most important part architecturally. The AI never touches the database directly - it only decides what to ask for and how to present the answer. All the actual numbers come from backend code.

```
User types a question
        ↓
AI (LLM) reads the question and decides:
  "This is a data query" → calls query_analytics tool
  "This is a forecast"   → calls forecast_demand tool
        ↓
Your backend executes the actual computation
(real SQL queries, real math - NOT the AI making up numbers)
        ↓
Results go back to the AI
        ↓
AI formats a human-readable answer + picks a chart type
        ↓
Frontend renders: text + chart + explanation
```

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                 │
└────────────────────────────┬────────────────────────────┘
                             │ REST API Call
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                    │
│                                                         │
│  1. User Question ──► AI Orchestrator (LLM)             │
│                             │                           │
│                             ▼ Uses OpenAI Function Call │
│                      Selects Tool Spec                  │
│                        /          \                     │
│                       ▼            ▼                    │
│            ┌──────────────┐     ┌──────────────┐        │
│            │  Query Tool  │     │ Forecast Tool│        │
│            └──────┬───────┘     └──────┬───────┘        │
│                   │                    │                │
│                   └──────────┬─────────┘                │
│                              ▼                          │
│                   Structured Query Builder              │
│                 (No raw AI SQL execution)               │
│                              │                          │
└──────────────────────────────┼──────────────────────────┘
                               │ Parameterized SQL Query
                               ▼
┌─────────────────────────────────────────────────────────┐
│                    DATABASE (PostgreSQL)                │
│              (the CSV loaded into a real database)      │
└─────────────────────────────────────────────────────────┘
```

**API surface:**
- `/api/dashboard/*` → direct SQL queries → KPIs & charts
- `/api/chat` → AI orchestrator → tool selection → SQL → result
- `/api/forecast` → forecasting model → predictions

### Guiding AI Principles

1. **AI as Router, Not Data Generator**: The LLM *never* fabricates statistical metrics. It interprets user intent, calls registered backend tools with structured parameters, and formats the output.
2. **Safe Query Construction**: The AI produces JSON query specs (filters, metrics, group_by). The Python backend validates these specs and constructs safe, parameterized SQLAlchemy queries.
3. **Transparent Explainability**: Every query response is accompanied by metadata explaining *how* the answer was derived - filters, metric, group-by, and computation method.

### One Registry, Three AI Surfaces

The standout design decision: **one analytics registry powers every AI surface** - the dashboard, the internal chat agent, and external AI clients all answer from the same code. No drift, no duplicate logic.

```
                    Scenario Registry + Runner
              (single source of truth - app/scenarios/)
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   REST adapter       OpenAI adapter      MCP adapter
   /api/dashboard     /api/chat           /mcp
          │                 │                 │
          ▼                 ▼                 ▼
   Dashboard page    Internal chat       External AI
   (browser)         (OpenAI GPT-4o      (Claude Code,
                     function calling)    Cursor, ChatGPT)
```

The registry holds two kinds of analytics:

- **Curated scenario catalog** - a fixed library of verified analytics (delay rate by carrier, on-time trend, p90 delivery, revenue Pareto, etc.). Each scenario declares its own SQL, chart type, and explanation template. Deterministic, safe, fully explainable.
- **Open-ended query tool** - for ad-hoc questions the catalog doesn't cover, the AI emits a structured spec `{metric, group_by, filters}` and the backend builds parameterized SQL. Still no raw AI SQL.

**Why three adapters?** Different AI clients speak different protocols:
- The **dashboard** is a browser - it calls REST.
- The **internal `/chat` agent** uses OpenAI function calling (GPT-4o invokes Python tool functions).
- **External AI clients** (Claude Code, Cursor, ChatGPT) speak MCP and connect to `/mcp`.

But all three adapters are thin wrappers over the same `runner.run(scenario_id)` call. Ask "which carrier has the highest delay rate?" in the web chat, in the dashboard, or from Claude Code connected to `/mcp` - identical answer, identical SQL, identical explanation.

### Scenario Catalog

The registry holds **33 scenarios** seeded by data exploration (`server/data/explorer.py`). Each is a runnable analytics unit the AI can pick (via `run_scenario`) and the dashboard can render. Every scenario appears identically in the explorer, this catalog, and the agent's system prompt.

**Reliability & performance (8)**
| id | answers | chart |
|---|---|---|
| `delay_rate_by_carrier` | Which carrier has the highest delay rate? | bar |
| `delay_rate_by_region` | Which region has the worst delivery performance? | bar |
| `warehouse_performance` | Which warehouse has the worst delay rate? | bar |
| `on_time_trend` | Is delivery performance improving over the year? | line |
| `delivery_time_percentiles` | How long do most orders take? (p50/p90/p95) | stat |
| `exception_deepdive` | Show all exception orders and the carriers they hit | table |
| `delay_rate_by_month` | Which months are worst for delays? | bar |
| `delivery_time_by_month` | Does delivery slow down seasonally? | line |

**Carrier deep-dive (4)**
| id | answers | chart |
|---|---|---|
| `carrier_market_share` | Which carrier handles the most orders? | pie |
| `avg_delivery_time_by_carrier` | Which carrier is fastest / slowest? | bar |
| `revenue_by_carrier` | Which carrier drives the most revenue? | bar |
| `carrier_reliability_trend` | Is each carrier improving or degrading over time? | multi-line |

**Volume & revenue (8)**
| id | answers | chart |
|---|---|---|
| `order_volume_by_month` | Show order volume trend over 2025 | area |
| `delivery_performance_by_month` | Delivered vs delayed each month | stacked bar |
| `order_volume_by_region` | Which region orders the most? | bar |
| `revenue_by_region` | Revenue by region | bar |
| `revenue_by_category` | Which category drives most revenue? | bar |
| `top_clients` | Who are our top clients by orders? | bar |
| `revenue_pareto` | What share of revenue comes from top clients? | stat |
| `busiest_routes` | What are our busiest shipping lanes? | bar |

**Routes & delivery (2)**
| id | answers | chart |
|---|---|---|
| `slowest_routes` | Which routes take the longest? | bar |
| `delivery_time_distribution` | How is delivery time distributed? | histogram |

**Category & product (5)**
| id | answers | chart |
|---|---|---|
| `avg_order_value_by_category` | Which category has the highest avg order value? | bar |
| `top_skus` | What are our most-ordered SKUs? | bar |
| `quantity_distribution` | What is the typical order size? | histogram |
| `sku_concentration` | How concentrated is our SKU catalog? | stat |
| `category_x_region` | Where does each category sell? (crosstab) | heatmap |

**Operations & status (5)**
| id | answers | chart |
|---|---|---|
| `status_distribution` | Order status breakdown | donut |
| `day_of_week_pattern` | Which days get the most orders? | bar |
| `order_value_distribution` | How are order values distributed? | histogram |
| `promo_vs_nonpromo` | Do promo orders delay more than non-promo? | bar |
| `delivery_time_by_region` | Delivery speed by region | bar |

**Forecast (1)**
| id | answers | chart |
|---|---|---|
| `forecast_demand` | Predict demand for a category for the next N months | line (historical + projection) |

The curated catalog (32 analytics + 1 forecast) covers the vast majority of real questions; the open-ended query tool handles anything it doesn't.

---

*That's the whole project. Dashboard, chat, forecast - one dataset, three ways to look at it.*
