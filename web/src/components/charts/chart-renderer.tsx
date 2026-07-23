"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cloneElement, createContext, useContext, useLayoutEffect, useRef, useState, type ReactElement } from "react";

import type { ChartType } from "@/lib/types";

const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#f43f5e", "#8b5cf6"];

const AXIS = { stroke: "#94a3b8", fontSize: 11, tickLine: false };
const GRID = "#eef2f7";

const ChartHeightContext = createContext(260);

interface Props {
  chartType: ChartType;
  data: Record<string, unknown>[];
  height?: number;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
const CURRENCY_KEYS = ["revenue", "value", "price", "avg_value"];
const PERCENT_KEYS = ["rate", "share", "on_time"];

function formatTipValue(name: string, value: unknown): string {
  if (typeof value !== "number") return String(value ?? "");
  const key = String(name).toLowerCase();
  if (CURRENCY_KEYS.some((k) => key.includes(k))) {
    return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  }
  if (PERCENT_KEYS.some((k) => key.includes(k))) {
    return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      {label != null && label !== "" && (
        <div className="mb-1 font-medium text-foreground">{String(label)}</div>
      )}
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center gap-2 text-muted-foreground">
          <span className="size-2 rounded-full" style={{ background: p.color || p.fill }} />
          <span>{prettify(String(p.name))}</span>
          <span className="ml-auto font-medium text-foreground tabular-nums">
            {formatTipValue(String(p.name), p.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

const TOOLTIP = <ChartTooltip />;
const CURSOR = { fill: "rgba(16,185,129,0.06)" };

/** Build legend items (label + color) from a chart's value/series keys. */
function seriesItems(valueKeys: string[]) {
  return valueKeys.map((k, i) => ({ label: prettify(k), color: COLORS[i % COLORS.length] }));
}

/** Wrapping legend — recharts' <Legend> doesn't wrap and overflows narrow cards. */
function LegendWrap({ items }: { items: { label: string; color: string }[] }) {
  if (!items.length) return null;
  return (
    <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 pt-1 text-[11px] text-muted-foreground">
      {items.map((it, i) => (
        <span key={i} className="inline-flex items-center gap-1.5">
          <span className="size-2 rounded-full" style={{ background: it.color }} />
          {it.label}
        </span>
      ))}
    </div>
  );
}

export function ChartRenderer({ chartType, data, height = 260 }: Props) {
  if (!data.length) {
    return <div className="py-10 text-center text-sm text-muted-foreground">No data</div>;
  }

  return (
    <ChartHeightContext.Provider value={height}>
      {render(chartType, data)}
    </ChartHeightContext.Provider>
  );
}

function render(chartType: ChartType, data: Record<string, unknown>[]) {
  switch (chartType) {
    case "bar":
    case "histogram":
      return <Bars data={data} />;
    case "stacked bar":
      return <Bars data={data} stacked />;
    case "line":
    case "multi-line":
      return <Lines data={data} />;
    case "area":
      return <Areas data={data} />;
    case "pie":
    case "donut":
      return <PieChartView data={data} donut={chartType === "donut"} />;
    case "stat":
      return <StatView data={data} />;
    case "table":
      return <TableView data={data} />;
    case "heatmap":
      return <Heatmap data={data} />;
    case "forecast":
      return <Forecast data={data} />;
    default:
      return <TableView data={data} />;
  }
}

function columns(data: Record<string, unknown>[]) {
  const keys = Object.keys(data[0]);
  return { labelKey: keys[0], valueKeys: keys.slice(1) };
}

function Bars({ data, stacked }: { data: Record<string, unknown>[]; stacked?: boolean }) {
  const { labelKey, valueKeys } = columns(data);
  return (
    <div>
      <Chart>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
          <XAxis dataKey={labelKey} {...AXIS} />
          <YAxis {...AXIS} />
          <Tooltip content={TOOLTIP} cursor={CURSOR} />
          {valueKeys.map((k, i) => (
            <Bar
              key={k}
              dataKey={k}
              stackId={stacked ? "a" : undefined}
              fill={COLORS[i % COLORS.length]}
              radius={stacked ? undefined : [4, 4, 0, 0]}
              maxBarSize={48}
            />
          ))}
        </BarChart>
      </Chart>
      {valueKeys.length > 1 && <LegendWrap items={seriesItems(valueKeys)} />}
    </div>
  );
}

function Lines({ data }: { data: Record<string, unknown>[] }) {
  const { labelKey, valueKeys } = columns(data);
  return (
    <div>
      <Chart>
        <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
          <XAxis dataKey={labelKey} {...AXIS} />
          <YAxis {...AXIS} />
          <Tooltip content={TOOLTIP} cursor={{ stroke: "#10b981", strokeOpacity: 0.2 }} />
          {valueKeys.map((k, i) => (
            <Line
              key={k}
              type="monotone"
              dataKey={k}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </Chart>
      {valueKeys.length > 1 && <LegendWrap items={seriesItems(valueKeys)} />}
    </div>
  );
}

function Areas({ data }: { data: Record<string, unknown>[] }) {
  const { labelKey, valueKeys } = columns(data);
  return (
    <div>
      <Chart>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            {valueKeys.map((k, i) => (
              <linearGradient key={k} id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.3} />
                <stop offset="100%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.02} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
          <XAxis dataKey={labelKey} {...AXIS} />
          <YAxis {...AXIS} />
          <Tooltip content={TOOLTIP} cursor={{ stroke: "#10b981", strokeOpacity: 0.2 }} />
          {valueKeys.map((k, i) => (
            <Area
              key={k}
              type="monotone"
              dataKey={k}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              fill={`url(#grad-${i})`}
            />
          ))}
        </AreaChart>
      </Chart>
      {valueKeys.length > 1 && <LegendWrap items={seriesItems(valueKeys)} />}
    </div>
  );
}

function PieChartView({ data, donut }: { data: Record<string, unknown>[]; donut?: boolean }) {
  const { labelKey, valueKeys } = columns(data);
  const valueKey = valueKeys[0];
  return (
    <div>
      <Chart>
        <PieChart>
          <Pie
            data={data}
            dataKey={valueKey}
            nameKey={labelKey}
            innerRadius={donut ? 48 : 0}
            outerRadius={72}
            paddingAngle={donut ? 2 : 0}
            cx="50%"
            cy="50%"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={TOOLTIP} />
          <XAxis hide />
          <YAxis hide />
        </PieChart>
      </Chart>
      <LegendWrap
        items={data.map((row, i) => ({
          label: prettify(String(row[labelKey])),
          color: COLORS[i % COLORS.length],
        }))}
      />
    </div>
  );
}

function StatView({ data }: { data: Record<string, unknown>[] }) {
  if (data.length === 1) {
    const entries = Object.entries(data[0]);
    return (
      <div className="grid grid-cols-2 gap-3 py-2 sm:grid-cols-3">
        {entries.map(([k, v]) => (
          <div key={k} className="rounded-md border bg-muted/30 px-3 py-2">
            <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              {prettify(k)}
            </div>
            <div className="mt-0.5 text-xl font-semibold tabular-nums">{formatVal(v)}</div>
          </div>
        ))}
      </div>
    );
  }
  // multi-row stat (e.g. revenue_pareto) → top-N bar
  const { labelKey, valueKeys } = columns(data);
  const top = [...data].sort(
    (a, b) => Number(b[valueKeys[0]]) - Number(a[valueKeys[0]])
  );
  return (
    <ul className="space-y-1.5 py-1">
      {top.slice(0, 8).map((row, i) => (
        <li key={i} className="flex items-center justify-between gap-3 text-sm">
          <span className="truncate text-muted-foreground">{String(row[labelKey])}</span>
          <span className="font-medium tabular-nums">{formatVal(row[valueKeys[0]])}</span>
        </li>
      ))}
    </ul>
  );
}

function TableView({ data }: { data: Record<string, unknown>[] }) {
  const keys = Object.keys(data[0]);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
            {keys.map((k) => (
              <th key={k} className="px-2 py-1.5 font-medium">
                {prettify(k)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 50).map((row, i) => (
            <tr key={i} className="border-b last:border-0">
              {keys.map((k) => (
                <td key={k} className="px-2 py-1.5 tabular-nums">
                  {formatVal(row[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Heatmap({ data }: { data: Record<string, unknown>[] }) {
  // long-form {row, col, value} → colored grid
  const rowKey = Object.keys(data[0])[0];
  const colKey = Object.keys(data[0])[1];
  const valKey = Object.keys(data[0])[2];
  const rows = Array.from(new Set(data.map((d) => String(d[rowKey]))));
  const cols = Array.from(new Set(data.map((d) => String(d[colKey]))));
  const cell = (r: string, c: string) =>
    data.find((d) => String(d[rowKey]) === r && String(d[colKey]) === c)?.[valKey];
  const max = Math.max(...data.map((d) => Number(d[valKey])), 1);
  return (
    <div className="overflow-x-auto py-1">
      <table className="border-collapse text-xs">
        <thead>
          <tr>
            <th className="px-2 py-1" />
            {cols.map((c) => (
              <th key={c} className="px-2 py-1 font-medium text-muted-foreground">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r}>
              <td className="px-2 py-1 font-medium text-muted-foreground">{r}</td>
              {cols.map((c) => {
                const v = cell(r, c);
                const op = v != null ? Math.max(0.08, Number(v) / max) : 0;
                return (
                  <td key={c} className="p-0.5 text-center">
                    <div
                      className="flex h-8 min-w-9 items-center justify-center rounded tabular-nums"
                      style={{
                        backgroundColor: `rgba(59, 130, 246, ${op})`,
                        color: op > 0.5 ? "#fff" : "#374151",
                      }}
                      title={v != null ? String(v) : ""}
                    >
                      {v != null ? String(v) : ""}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Forecast({ data }: { data: Record<string, unknown>[] }) {
  // Each row is historical (actual + per-method FITTED values) or forecast
  // (per-method future values). Pivot into per-month rows with an `actual`
  // column and one continuous column per method, so each method renders as a
  // single line spanning history (fitted) + future (forecast).
  type Row = { actual: number | null; exp: number | null; linear: number | null; ma: number | null };
  const byMonth = new Map<string, Row>();
  const num = (v: unknown) =>
    typeof v === "number" ? v : v == null || v === "" ? null : Number(v);
  for (const row of data) {
    const month = String(row.month);
    const isHist = String(row.type) === "historical";
    const entry = byMonth.get(month) ?? { actual: null, exp: null, linear: null, ma: null };
    if (isHist) {
      entry.actual = num(row.quantity);
      entry.exp = num((row as Record<string, unknown>).exp);
      entry.linear = num((row as Record<string, unknown>).linear);
      entry.ma = num((row as Record<string, unknown>).moving_average);
    } else {
      entry.exp = num((row as Record<string, unknown>).exp ?? row.quantity);
      entry.linear = num((row as Record<string, unknown>).linear);
      entry.ma = num((row as Record<string, unknown>).moving_average);
    }
    byMonth.set(month, entry);
  }
  const pivoted = Array.from(byMonth, ([month, v]) => ({
    month,
    historical: v.actual,
    exp: v.exp,
    linear: v.linear,
    "moving avg": v.ma,
  }));
  return (
    <div>
      <Chart>
        <LineChart data={pivoted} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
          <XAxis dataKey="month" {...AXIS} />
          <YAxis {...AXIS} />
          <Tooltip content={TOOLTIP} cursor={{ stroke: "#10b981", strokeOpacity: 0.2 }} />
          <Line type="monotone" dataKey="historical" name="Actual" stroke="#10b981" strokeWidth={2.5} dot={{ r: 2 }} connectNulls />
          <Line type="monotone" dataKey="exp" name="Exp. smoothing" stroke="#10b981" strokeOpacity={0.55} strokeWidth={2} strokeDasharray="6 4" dot={false} connectNulls />
          <Line type="monotone" dataKey="linear" name="Linear regression" stroke="#3b82f6" strokeWidth={1.5} strokeDasharray="4 3" dot={false} connectNulls />
          <Line type="monotone" dataKey="moving avg" name="Moving avg" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="4 3" dot={false} connectNulls />
        </LineChart>
      </Chart>
      <LegendWrap
        items={[
          { label: "Actual", color: "#10b981" },
          { label: "Exp. smoothing", color: "rgba(16,185,129,0.55)" },
          { label: "Linear regression", color: "#3b82f6" },
          { label: "Moving avg", color: "#f59e0b" },
        ]}
      />
    </div>
  );
}

function Chart({ children }: { children: ReactElement<any> }) {
  const height = useContext(ChartHeightContext);
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<{ w: number; h: number } | null>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => setSize({ w: el.clientWidth, h: el.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div ref={ref} style={{ height }} className="w-full">
      {size && size.w > 0 && size.h > 0
        ? cloneElement(children, { width: size.w, height: size.h })
        : null}
    </div>
  );
}

function prettify(key: string) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

function formatVal(v: unknown) {
  if (v == null) return "—";
  if (typeof v === "number") return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(v);
}
