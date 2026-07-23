"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import type { ChartType } from "@/lib/types";

const ChartRenderer = dynamic(
  () => import("./chart-renderer").then((m) => m.ChartRenderer),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[260px] w-full rounded-md" />,
  }
);

interface Props {
  chartType: ChartType;
  data: Record<string, unknown>[];
}

export function DynamicChart({ chartType, data }: Props) {
  return <ChartRenderer chartType={chartType} data={data} />;
}
