import type { ChartResponse, ChatResponse, KpiResponse, KpiTrends, ScenarioMeta } from "./types";

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

export interface ChatStreamHandlers {
  onStatus?: (step: string) => void;
  onTool?: (label: string) => void;
  onToken?: (delta: string) => void;
  onDone?: (payload: ChatResponse) => void;
  onError?: (detail: string) => void;
}

async function consumeChatStream(res: Response, h: ChatStreamHandlers): Promise<void> {
  const reader = res.body?.getReader();
  if (!reader) throw new Error("no response body");
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      let parsed: Record<string, unknown>;
      try {
        parsed = JSON.parse(data);
      } catch {
        continue;
      }
      switch (event) {
        case "status":
          h.onStatus?.(String(parsed.step ?? ""));
          break;
        case "tool":
          h.onTool?.(String(parsed.label ?? parsed.name ?? ""));
          break;
        case "token":
          h.onToken?.(String(parsed.delta ?? ""));
          break;
        case "done":
          h.onDone?.(parsed as unknown as ChatResponse);
          break;
        case "error":
          h.onError?.(String(parsed.detail ?? "stream error"));
          break;
      }
    }
  }
}

export const clientApi = {
  kpis: () => clientGet<KpiResponse>("/api/dashboard/kpis"),
  kpiTrends: () => clientGet<KpiTrends>("/api/dashboard/kpi-trends"),
  scenarios: () => clientGet<ScenarioMeta[]>("/api/dashboard/scenarios"),
  chart: (id: string) => clientGet<ChartResponse>(`/api/dashboard/charts/${id}`),
  chat: (question: string) =>
    fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }).then(async (res) => {
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `API ${res.status}`);
      }
      return (await res.json()) as ChatResponse;
    }),
  chatStream: async (question: string, h: ChatStreamHandlers): Promise<void> => {
    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail ?? `API ${res.status}`);
    }
    await consumeChatStream(res, h);
  },
};
