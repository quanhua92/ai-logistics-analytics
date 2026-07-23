import { AlertCircle, AlertTriangle, Boxes, DollarSign, Gauge, Navigation, PackageCheck, Timer } from "lucide-react";

import type { KpiResponse, KpiTrends } from "@/lib/types";
import type { KpiTone } from "./kpi-card";
import { KpiCard } from "./kpi-card";

interface Item {
  label: string;
  value: string;
  hint?: string;
  icon: typeof Boxes;
  tone: KpiTone;
  trendKey: string;
  invertDelta?: boolean;
}

export function KpiGrid({ kpis, trends }: { kpis: KpiResponse; trends?: KpiTrends }) {
  const num = (v: number | undefined | null) => (v ?? 0).toLocaleString();
  const items: Item[] = [
    { label: "Total Orders", value: num(kpis.total_orders), icon: Boxes, tone: "neutral", trendKey: "total_orders" },
    { label: "Delivered", value: num(kpis.delivered), icon: PackageCheck, tone: "emerald", trendKey: "delivered" },
    { label: "Delayed", value: num(kpis.delayed), icon: AlertTriangle, tone: "rose", trendKey: "delayed", invertDelta: true },
    { label: "Exceptions", value: num(kpis.exceptions), icon: AlertCircle, tone: "amber", trendKey: "exceptions", invertDelta: true },
    {
      label: "On-time Rate",
      value: kpis.on_time_rate != null ? `${kpis.on_time_rate.toFixed(1)}%` : "—",
      hint: "of completed",
      icon: Gauge,
      tone: "emerald",
      trendKey: "on_time_rate",
    },
    {
      label: "Avg Delivery",
      value: kpis.avg_delivery_days != null ? `${kpis.avg_delivery_days} d` : "—",
      icon: Timer,
      tone: "blue",
      trendKey: "avg_delivery_days",
      invertDelta: true,
    },
    { label: "In Transit", value: num(kpis.in_transit), icon: Navigation, tone: "violet", trendKey: "in_transit" },
    {
      label: "Revenue",
      value: `$${num(kpis.total_revenue)}`,
      icon: DollarSign,
      tone: "blue",
      trendKey: "total_revenue",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {items.map((it) => {
        const trend = trends?.[it.trendKey];
        return (
          <KpiCard
            key={it.label}
            {...it}
            series={trend?.series.map((p) => p.value)}
            delta={trend?.delta_pct}
          />
        );
      })}
    </div>
  );
}
