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
  | "heatmap"
  | "forecast";

export interface KpiResponse {
  total_orders: number;
  delivered: number;
  delayed: number;
  exceptions: number;
  in_transit: number;
  on_time_rate: number;
  avg_delivery_days: number | null;
  total_revenue: number;
}

export interface KpiTrendPoint {
  month: string;
  value: number;
}

export interface KpiTrend {
  series: KpiTrendPoint[];
  delta_pct: number | null;
}

export type KpiTrends = Record<string, KpiTrend>;

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

export interface ChatExplanation {
  metric?: string;
  dimensions?: string[];
  method?: string;
  filters_used?: { field: string; op: string; value: unknown }[];
  data_summary?: { row_count: number };
  category?: string;
  horizon_months?: number;
  methodology?: string;
  recommendation?: { peak_forecast_units?: number; safety_stock_units?: number; note?: string };
  [key: string]: unknown;
}

export interface ChatResponse {
  answer: string;
  chart_type: ChartType | null;
  chart_data: Record<string, unknown>[] | null;
  explanation: ChatExplanation | null;
  scenario_id: string | null;
  title: string | null;
}

export interface HistoricalPoint {
  month: string;
  quantity: number;
  linear?: number | null;
  moving_average?: number | null;
  exp?: number | null;
}

export interface ForecastPoint {
  month: string;
  quantity: number;
  linear?: number | null;
  moving_average?: number | null;
  exp?: number | null;
}

export interface ForecastRecommendation {
  peak_forecast_units: number;
  safety_stock_units: number;
  note: string;
}

export interface ForecastReadiness {
  mean_monthly_quantity: number;
  std_dev: number;
  data_points: number;
}

export interface ForecastResponse {
  category: string;
  horizon_months: number;
  historical: HistoricalPoint[];
  forecast: ForecastPoint[];
  recommendation: ForecastRecommendation;
  methodology: string;
  readiness: ForecastReadiness;
}
