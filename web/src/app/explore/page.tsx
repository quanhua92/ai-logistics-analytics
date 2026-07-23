import { serverApi } from "@/lib/api";
import { Explorer, type ChartGroup } from "@/components/dashboard/explorer";
import type { ChartResponse } from "@/lib/types";

export const revalidate = 60;

export default async function ExplorePage() {
  const scenarios = await serverApi.scenarios();
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
        <h1 className="text-2xl font-semibold tracking-tight">Explore</h1>
        <p className="text-sm text-muted-foreground">
          All {charts.length} analytics across {groups.length} groups.
        </p>
      </header>

      <Explorer groups={groups} />
    </div>
  );
}
