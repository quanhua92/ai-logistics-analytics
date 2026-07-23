import Link from "next/link";

import { serverApi } from "@/lib/api";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { ChartPanel } from "@/components/dashboard/chart-panel";

export const revalidate = 60;

const CURATED = [
  "order_volume_by_month",
  "delivery_performance_by_month",
  "delay_rate_by_carrier",
  "status_distribution",
  "revenue_by_category",
  "top_clients",
];

export default async function Home() {
  const [kpis, charts] = await Promise.all([
    serverApi.kpis(),
    Promise.all(CURATED.map((id) => serverApi.chart(id))),
  ]);

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          {kpis.total_orders} orders across the network. On-time {kpis.on_time_rate.toFixed(1)}%.
        </p>
      </header>

      <KpiGrid kpis={kpis} />

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Overview
          </h2>
          <Link
            href="/explore"
            className="text-xs font-medium text-foreground underline-offset-4 hover:underline"
          >
            Explore all 32 →
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {charts.map((c) => (
            <ChartPanel key={c.id} chart={c} />
          ))}
        </div>
      </section>
    </div>
  );
}
