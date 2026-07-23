export type ChartType =
  | "bar"
  | "line"
  | "area"
  | "stacked bar"
  | "histogram"
  | "pie"
  | "donut"
  | "multi-line"
  | "stat"
  | "table"
  | "heatmap";

export interface KpiResponse {
  total_orders: number;
  delivered: number;
  delayed: number;
  in_transit: number;
  on_time_rate: number;
  avg_delivery_days: number | null;
  total_revenue: number;
}

export interface ScenarioMeta {
  id: string;
  group: string;
  title: string;
  question: string;
  chart_type: ChartType;
}

export interface ChartExplanation {
  metric: string;
  dimensions: string[];
  method: string;
  [key: string]: unknown;
}

export interface ChartResponse {
  id: string;
  title: string;
  question: string;
  chart_type: ChartType;
  data: Record<string, unknown>[];
  explanation: ChartExplanation;
}
