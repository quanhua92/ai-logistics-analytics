import type { ChartResponse, KpiResponse, ScenarioMeta } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

/** Server-side cached fetch (Next 16 fetch caching). Revalidate every 60s. */
async function getCached<T>(path: string): Promise<T> {
  return get<T>(path, { next: { revalidate: 60 } });
}

export const api = {
  kpis: () => getCached<KpiResponse>("/api/dashboard/kpis"),
  scenarios: () => getCached<ScenarioMeta[]>("/api/dashboard/scenarios"),
  chart: (id: string) => getCached<ChartResponse>(`/api/dashboard/charts/${id}`),
};
