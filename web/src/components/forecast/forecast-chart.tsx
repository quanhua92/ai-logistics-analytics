"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cloneElement, useLayoutEffect, useRef, useState, type ReactElement } from "react";

import type { ForecastResponse } from "@/lib/types";

const AXIS = { stroke: "#94a3b8", fontSize: 11, tickLine: false };
const GRID = "#eef2f7";

/** Merge historical + forecast into per-month rows with one column per series. */
function pivot(data: ForecastResponse) {
  const byMonth = new Map<string, Record<string, number | null>>();
  for (const h of data.historical) {
    byMonth.set(h.month, {
      historical: h.quantity,
      exp: null,
      linear: null,
      moving_average: null,
    });
  }
  for (const f of data.forecast) {
    const row =
      byMonth.get(f.month) ?? {
        historical: null,
        exp: null,
        linear: null,
        moving_average: null,
      };
    row.exp = f.quantity;
    row.linear = f.linear ?? null;
    row.moving_average = f.moving_average ?? null;
    byMonth.set(f.month, row);
  }
  return Array.from(byMonth, ([month, v]) => ({ month, ...v }));
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <div className="mb-1 font-medium text-foreground">{label}</div>
      {payload
        .filter((p: any) => p.value != null)
        .map((p: any) => (
          <div key={p.dataKey} className="flex items-center gap-2 text-muted-foreground">
            <span className="size-2 rounded-full" style={{ background: p.color }} />
            <span>{p.name}</span>
            <span className="ml-auto font-medium tabular-nums text-foreground">
              {Number(p.value).toFixed(1)}
            </span>
          </div>
        ))}
    </div>
  );
}

function Sizer({ height, children }: { height: number; children: ReactElement<any> }) {
  const ref = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => setW(el.clientWidth);
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return (
    <div ref={ref} style={{ height }} className="w-full">
      {w > 0 ? cloneElement(children, { width: w, height }) : null}
    </div>
  );
}

export function ForecastChart({ data, height = 300 }: { data: ForecastResponse; height?: number }) {
  const rows = pivot(data);
  return (
    <Sizer height={height}>
      <LineChart data={rows} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
        <XAxis dataKey="month" {...AXIS} />
        <YAxis {...AXIS} />
        <Tooltip content={<ChartTooltip />} />
        <Legend
          verticalAlign="bottom"
          height={28}
          iconType="line"
          iconSize={14}
          wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
        />
        <Line
          type="monotone"
          dataKey="historical"
          name="Historical"
          stroke="#10b981"
          strokeWidth={2.5}
          dot={{ r: 2 }}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="exp"
          name="Exp. smoothing (primary)"
          stroke="#10b981"
          strokeOpacity={0.55}
          strokeWidth={2}
          strokeDasharray="6 4"
          dot={{ r: 2 }}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="linear"
          name="Linear regression"
          stroke="#3b82f6"
          strokeWidth={1.5}
          strokeDasharray="4 3"
          dot={false}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="moving_average"
          name="3-month moving avg"
          stroke="#f59e0b"
          strokeWidth={1.5}
          strokeDasharray="4 3"
          dot={false}
          connectNulls
        />
      </LineChart>
    </Sizer>
  );
}
