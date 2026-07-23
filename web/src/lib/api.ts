import type {
  ChartResponse,
  ChatResponse,
  ChartType,
  ForecastResponse,
  KpiResponse,
  KpiTrends,
  ScenarioMeta,
} from "./types";

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
  forecastCategories: () => serverGet<string[]>("/api/forecast/categories"),
  forecast: (category: string, horizon: number) =>
    serverGet<ForecastResponse>(`/api/forecast?category=${encodeURIComponent(category)}&horizon=${horizon}`),
};

export interface ChatStreamHandlers {
  onStatus?: (step: string) => void;
  onTool?: (name: string, label: string, args: unknown) => void;
  onToken?: (delta: string) => void;
  onThinking?: (delta: string) => void;
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
          h.onTool?.(
            String(parsed.name ?? ""),
            String(parsed.label ?? parsed.name ?? ""),
            parsed.args ?? {}
          );
          break;
        case "token":
          h.onToken?.(String(parsed.delta ?? ""));
          break;
        case "thinking":
          h.onThinking?.(String(parsed.delta ?? ""));
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

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

const KEY_STORAGE = "logistics.chat.keyHash";

/** Chat access-key helpers. Only the SHA-256 hash is stored/sent — never the raw key. */
export function getChatKeyHash(): string | null {
  try {
    return localStorage.getItem(KEY_STORAGE);
  } catch {
    return null;
  }
}
export function setChatKeyHash(hash: string) {
  try {
    localStorage.setItem(KEY_STORAGE, hash);
  } catch {
    /* storage unavailable */
  }
}
export function clearChatKeyHash() {
  try {
    localStorage.removeItem(KEY_STORAGE);
  } catch {
    /* ignore */
  }
}

export class UnauthorizedError extends Error {
  constructor() {
    super("invalid or missing access key");
    this.name = "UnauthorizedError";
  }
}
export class RateLimitError extends Error {
  constructor() {
    super("Too many requests — please slow down.");
    this.name = "RateLimitError";
  }
}

function chatHeaders(): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const hash = getChatKeyHash();
  if (hash) h["X-Chat-Key"] = hash;
  return h;
}

async function chatHttpError(res: Response): Promise<Error> {
  if (res.status === 401) return new UnauthorizedError();
  if (res.status === 429) return new RateLimitError();
  const detail = await res.json().catch(() => ({}));
  return new Error(detail.detail ?? `API ${res.status}`);
}

async function postChat(
  path: string,
  question: string,
  history: ChatTurn[],
  conversationId: string,
  signal?: AbortSignal
) {
  return fetch(path, {
    method: "POST",
    headers: chatHeaders(),
    body: JSON.stringify({ question, history, conversation_id: conversationId }),
    signal,
  });
}

export interface ConversationTurn {
  question: string;
  answer: string;
  tool_calls?: { name: string; label?: string; status?: string }[];
  chart_type?: ChartType | null;
  chart_data?: Record<string, unknown>[] | null;
  explanation?: Record<string, unknown> | null;
  scenario_id?: string | null;
  title?: string | null;
  error?: string | null;
  ts?: string;
}

export interface ConversationSummary {
  conversation_id: string;
  first_question: string;
  turn_count: number;
  last_ts: string;
}

export const clientApi = {
  kpis: () => clientGet<KpiResponse>("/api/dashboard/kpis"),
  kpiTrends: () => clientGet<KpiTrends>("/api/dashboard/kpi-trends"),
  scenarios: () => clientGet<ScenarioMeta[]>("/api/dashboard/scenarios"),
  chart: (id: string) => clientGet<ChartResponse>(`/api/dashboard/charts/${id}`),
  listConversations: () => clientGet<ConversationSummary[]>("/api/chat"),
  getConversation: async (id: string) => {
    const res = await clientGet<{ conversation_id: string; turns: ConversationTurn[] }>(
      `/api/chat/${encodeURIComponent(id)}`
    );
    return res;
  },
  chat: async (question: string, history: ChatTurn[], conversationId: string) => {
    const res = await postChat("/api/chat", question, history, conversationId);
    if (!res.ok) throw await chatHttpError(res);
    return (await res.json()) as ChatResponse;
  },
  chatStream: async (
    question: string,
    history: ChatTurn[],
    conversationId: string,
    h: ChatStreamHandlers,
    signal?: AbortSignal
  ): Promise<void> => {
    const res = await postChat("/api/chat/stream", question, history, conversationId, signal);
    if (!res.ok) throw await chatHttpError(res);
    await consumeChatStream(res, h);
  },
  forecastCategories: () => clientGet<string[]>("/api/forecast/categories"),
  forecast: (category: string, horizon: number) =>
    clientGet<ForecastResponse>(
      `/api/forecast?category=${encodeURIComponent(category)}&horizon=${horizon}`
    ),
};
