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
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";

import type { ChartType } from "@/lib/types";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#f43f5e", "#8b5cf6"];

const AXIS = { stroke: "#9ca3af", fontSize: 11, tickLine: false };

interface Props {
  chartType: ChartType;
  data: Record<string, unknown>[];
}

export function DynamicChart({ chartType, data }: Props) {
  if (!data.length) {
    return <div className="py-10 text-center text-sm text-muted-foreground">No data</div>;
  }

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
    <Chart>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
        <XAxis dataKey={labelKey} {...AXIS} />
        <YAxis {...AXIS} />
        {valueKeys.map((k, i) => (
          <Bar
            key={k}
            dataKey={k}
            stackId={stacked ? "a" : undefined}
            fill={COLORS[i % COLORS.length]}
            radius={stacked ? undefined : [3, 3, 0, 0]}
            maxBarSize={48}
          />
        ))}
      </BarChart>
    </Chart>
  );
}

function Lines({ data }: { data: Record<string, unknown>[] }) {
  const { labelKey, valueKeys } = columns(data);
  return (
    <Chart>
      <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
        <XAxis dataKey={labelKey} {...AXIS} />
        <YAxis {...AXIS} />
        {valueKeys.map((k, i) => (
          <Line
            key={k}
            type="monotone"
            dataKey={k}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </Chart>
  );
}

function Areas({ data }: { data: Record<string, unknown>[] }) {
  const { labelKey, valueKeys } = columns(data);
  return (
    <Chart>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <defs>
          {valueKeys.map((k, i) => (
            <linearGradient key={k} id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.35} />
              <stop offset="100%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.02} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
        <XAxis dataKey={labelKey} {...AXIS} />
        <YAxis {...AXIS} />
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
  );
}

function PieChartView({ data, donut }: { data: Record<string, unknown>[]; donut?: boolean }) {
  const { labelKey, valueKeys } = columns(data);
  return (
    <Chart>
      <PieChart>
        <Pie
          data={data}
          dataKey={valueKeys[0]}
          nameKey={labelKey}
          innerRadius={donut ? 50 : 0}
          outerRadius={85}
          paddingAngle={donut ? 2 : 0}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <XAxis hide />
        <YAxis hide />
      </PieChart>
    </Chart>
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
                      {v != null ? v : ""}
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

function Chart({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        {children as React.ReactElement}
      </ResponsiveContainer>
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
