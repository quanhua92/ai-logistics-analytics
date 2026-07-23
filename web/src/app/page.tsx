import { serverApi } from "@/lib/api";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { Explorer, type ChartGroup } from "@/components/dashboard/explorer";
import type { ChartResponse } from "@/lib/types";

export const revalidate = 60;

export default async function Home() {
  const [kpis, scenarios] = await Promise.all([serverApi.kpis(), serverApi.scenarios()]);

  const charts = await Promise.all(scenarios.map((s) => serverApi.chart(s.id)));

  const order: string[] = [];
  const byGroup: Record<string, ChartResponse[]> = {};
  scenarios.forEach((s, i) => {
    if (!byGroup[s.group]) {
      byGroup[s.group] = [];
      order.push(s.group);
    }
    byGroup[s.group].push(charts[i]);
  });
  const groups: ChartGroup[] = order.map((name) => ({ name, charts: byGroup[name] }));

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Operational overview across {kpis.total_orders} orders. Explore {charts.length}{" "}
          analytics by group.
        </p>
      </header>

      <KpiGrid kpis={kpis} />

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Analytics explorer
        </h2>
        <Explorer groups={groups} />
      </section>
    </div>
  );
}
