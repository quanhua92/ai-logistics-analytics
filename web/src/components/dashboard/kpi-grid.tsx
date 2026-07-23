import { AlertCircle, AlertTriangle, Boxes, DollarSign, Gauge, Navigation, PackageCheck, Timer } from "lucide-react";

import type { KpiResponse } from "@/lib/types";
import type { KpiTone } from "./kpi-card";
import { KpiCard } from "./kpi-card";

interface Item {
  label: string;
  value: string;
  hint?: string;
  icon: typeof Boxes;
  tone: KpiTone;
}

export function KpiGrid({ kpis }: { kpis: KpiResponse }) {
  const num = (v: number | undefined | null) => (v ?? 0).toLocaleString();
  const items: Item[] = [
    { label: "Total Orders", value: num(kpis.total_orders), icon: Boxes, tone: "neutral" },
    { label: "Delivered", value: num(kpis.delivered), icon: PackageCheck, tone: "emerald" },
    {
      label: "Delayed",
      value: num(kpis.delayed),
      icon: AlertTriangle,
      tone: "rose",
    },
    {
      label: "Exceptions",
      value: num(kpis.exceptions),
      icon: AlertCircle,
      tone: "amber",
    },
    {
      label: "On-time Rate",
      value: kpis.on_time_rate != null ? `${kpis.on_time_rate.toFixed(1)}%` : "—",
      hint: "of completed",
      icon: Gauge,
      tone: "emerald",
    },
    {
      label: "Avg Delivery",
      value: kpis.avg_delivery_days != null ? `${kpis.avg_delivery_days} d` : "—",
      hint: "completed",
      icon: Timer,
      tone: "blue",
    },
    {
      label: "In Transit",
      value: num(kpis.in_transit),
      icon: Navigation,
      tone: "violet",
    },
    {
      label: "Revenue",
      value: `$${num(kpis.total_revenue)}`,
      icon: DollarSign,
      tone: "blue",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {items.map((it) => (
        <KpiCard key={it.label} {...it} />
      ))}
    </div>
  );
}
