import type { KpiResponse } from "@/lib/types";
import { KpiCard } from "./kpi-card";

export function KpiGrid({ kpis }: { kpis: KpiResponse }) {
  const items: {
    label: string;
    value: string;
    hint?: string;
    tone?: "default" | "warning";
  }[] = [
    { label: "Total Orders", value: kpis.total_orders.toLocaleString() },
    { label: "Delivered", value: kpis.delivered.toLocaleString() },
    {
      label: "Delayed",
      value: kpis.delayed.toLocaleString(),
      tone: "warning",
    },
    {
      label: "On-time Rate",
      value: `${kpis.on_time_rate.toFixed(1)}%`,
      hint: "delivered / completed",
    },
    {
      label: "Avg Delivery",
      value: kpis.avg_delivery_days != null ? `${kpis.avg_delivery_days} d` : "—",
      hint: "completed orders",
    },
    { label: "In Transit", value: kpis.in_transit.toLocaleString() },
    {
      label: "Revenue",
      value: `$${kpis.total_revenue.toLocaleString(undefined, {
        maximumFractionDigits: 0,
      })}`,
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
