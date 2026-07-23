"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChartPanel } from "./chart-panel";
import type { ChartResponse } from "@/lib/types";

export interface ChartGroup {
  name: string;
  charts: ChartResponse[];
}

export function Explorer({ groups }: { groups: ChartGroup[] }) {
  const first = groups[0]?.name;
  if (!first) return null;
  return (
    <Tabs defaultValue={first} className="w-full">
      <div className="overflow-x-auto pb-1">
        <TabsList className="flex h-9 w-max gap-1">
          {groups.map((g) => (
            <TabsTrigger key={g.name} value={g.name} className="text-xs">
              {g.name}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      {groups.map((g) => (
        <TabsContent key={g.name} value={g.name} className="mt-4">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {g.charts.map((c) => (
              <ChartPanel key={c.id} chart={c} />
            ))}
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}
