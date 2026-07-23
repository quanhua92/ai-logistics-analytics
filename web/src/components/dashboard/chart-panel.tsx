import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DynamicChart } from "@/components/charts/dynamic-chart";
import type { ChartResponse } from "@/lib/types";

export function ChartPanel({ chart }: { chart: ChartResponse }) {
  return (
    <Card className="shadow-card overflow-hidden">
      <CardHeader className="pb-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="text-[15px] font-semibold tracking-tight">
              {chart.title}
            </CardTitle>
            <CardDescription className="mt-0.5 text-xs">{chart.question}</CardDescription>
          </div>
          <Badge variant="secondary" className="hidden shrink-0 text-[10px] capitalize">
            {chart.chart_type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <DynamicChart chartType={chart.chart_type} data={chart.data} />
      </CardContent>
      <div className="border-t px-6 py-2 text-[11px] text-muted-foreground">
        {chart.explanation.method}
      </div>
    </Card>
  );
}
