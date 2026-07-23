import type { ChartResponse, KpiResponse, KpiTrends, ScenarioMeta } from "./types";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/** Server-side fetch (absolute URL) with Next.js cache + revalidate. */
async function serverGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return (await res.json()) as T;
}

/** Client-side fetch (relative URL) via the next.config rewrite proxy. */
async function clientGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return (await res.json()) as T;
}

export const serverApi = {
  kpis: () => serverGet<KpiResponse>("/api/dashboard/kpis"),
  kpiTrends: () => serverGet<KpiTrends>("/api/dashboard/kpi-trends"),
  scenarios: () => serverGet<ScenarioMeta[]>("/api/dashboard/scenarios"),
  chart: (id: string) => serverGet<ChartResponse>(`/api/dashboard/charts/${id}`),
};

export const clientApi = {
  kpis: () => clientGet<KpiResponse>("/api/dashboard/kpis"),
  kpiTrends: () => clientGet<KpiTrends>("/api/dashboard/kpi-trends"),
  scenarios: () => clientGet<ScenarioMeta[]>("/api/dashboard/scenarios"),
  chart: (id: string) => clientGet<ChartResponse>(`/api/dashboard/charts/${id}`),
};
