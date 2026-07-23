"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChartPanel } from "./chart-panel";
import type { ChartResponse } from "@/lib/types";

export interface ChartGroup {
  name: string;
  charts: ChartResponse[];
}

function shortLabel(name: string): string {
  return name.split(" & ")[0].replace(" deep-dive", "").trim();
}

export function Explorer({ groups }: { groups: ChartGroup[] }) {
  const first = groups[0]?.name;
  if (!first) return null;
  return (
    <Tabs defaultValue={first} className="w-full">
      <div className="sticky top-0 z-20 -mx-4 mb-1 bg-background/95 px-4 py-2 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="flex gap-2 overflow-x-auto [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <TabsList className="flex h-auto w-max gap-2 rounded-full bg-transparent p-0">
            {groups.map((g) => (
              <TabsTrigger
                key={g.name}
                value={g.name}
                className="shrink-0 whitespace-nowrap rounded-full border border-border bg-background px-3.5 py-1.5 text-xs font-medium text-muted-foreground shadow-none transition-colors data-[state=active]:border-primary data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                {shortLabel(g.name)}
                <span className="ml-1.5 tabular-nums opacity-60">{g.charts.length}</span>
              </TabsTrigger>
            ))}
          </TabsList>
        </div>
      </div>

      {groups.map((g) => (
        <TabsContent key={g.name} value={g.name} className="mt-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {g.charts.map((c) => (
              <ChartPanel key={c.id} chart={c} />
            ))}
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}
