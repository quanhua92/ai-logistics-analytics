import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DynamicChart } from "@/components/charts/dynamic-chart";
import type { ChartResponse } from "@/lib/types";

export function ChartPanel({ chart }: { chart: ChartResponse }) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{chart.title}</CardTitle>
        <CardDescription className="text-xs">{chart.question}</CardDescription>
      </CardHeader>
      <CardContent>
        <DynamicChart chartType={chart.chart_type} data={chart.data} />
      </CardContent>
      <div className="border-t px-6 py-2 text-[11px] text-muted-foreground">
        {chart.explanation.method}
      </div>
    </Card>
  );
}
