"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { clientApi, type ChatTurn } from "@/lib/api";
import type { ChatExplanation, ChartType } from "@/lib/types";

export interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  chartType?: ChartType | null;
  chartData?: Record<string, unknown>[] | null;
  explanation?: ChatExplanation | null;
  scenarioId?: string | null;
  error?: boolean;
  streaming?: boolean;
  status?: string | null;
  tools?: { name: string; label: string; args?: unknown }[];
  thinking?: string;
}

const STORAGE_KEY = "logistics.chat.conversationId";

/** Read the last-used conversation id from localStorage (no API call). */
export function getStoredConversationId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function persistId(id: string) {
  try {
    localStorage.setItem(STORAGE_KEY, id);
  } catch {
    /* storage may be unavailable */
  }
}

function loadOrCreateId(): string {
  if (typeof window === "undefined") return "";
  try {
    const existing = localStorage.getItem(STORAGE_KEY);
    if (existing) return existing;
  } catch {
    /* ignore */
  }
  const id =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `c-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  persistId(id);
  return id;
}

let _seq = 0;
const nextId = () => `m${++_seq}`;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState("");
  const controllerRef = useRef<AbortController | null>(null);

  /** Abort the in-flight stream (keeps whatever has streamed so far). */
  const stop = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  // Hydrate the conversation id from localStorage on mount (SSR-safe).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time browser-API hydration
    setConversationId(loadOrCreateId());
  }, []);

  const patch = useCallback((id: string, changes: Partial<ChatMessageData>) => {
    setMessages((m) => m.map((msg) => (msg.id === id ? { ...msg, ...changes } : msg)));
  }, []);

  const appendDelta = useCallback((id: string, delta: string) => {
    setMessages((m) =>
      m.map((msg) =>
        msg.id === id ? { ...msg, content: msg.content + delta, status: null } : msg
      )
    );
  }, []);

  const appendTool = useCallback((id: string, name: string, label: string, args: unknown) => {
    setMessages((m) =>
      m.map((msg) =>
        msg.id === id
          ? { ...msg, tools: [...(msg.tools ?? []), { name, label, args }], status: label }
          : msg
      )
    );
  }, []);

  const appendThinking = useCallback((id: string, delta: string) => {
    setMessages((m) =>
      m.map((msg) =>
        msg.id === id ? { ...msg, thinking: (msg.thinking ?? "") + delta } : msg
      )
    );
  }, []);

  const send = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || loading) return;

      // Prior completed text turns become the model's context.
      const history: ChatTurn[] = messages
        .filter((msg) => !msg.streaming && !msg.error && msg.content)
        .map((msg) => ({ role: msg.role, content: msg.content }));

      const userMsg: ChatMessageData = { id: nextId(), role: "user", content: q };
      const assistantId = nextId();
      const placeholder: ChatMessageData = {
        id: assistantId,
        role: "assistant",
        content: "",
        streaming: true,
      };
      setMessages((m) => [...m, userMsg, placeholder]);
      setLoading(true);

      const controller = new AbortController();
      controllerRef.current = controller;
      try {
        await clientApi.chatStream(
          q,
          history,
          conversationId,
          {
            onStatus: () => patch(assistantId, { status: "Thinking…" }),
            onTool: (name, label, args) => appendTool(assistantId, name, label, args),
            onToken: (delta) => appendDelta(assistantId, delta),
            onThinking: (delta) => appendThinking(assistantId, delta),
            onDone: (payload) =>
              patch(assistantId, {
                content: payload.answer,
                chartType: payload.chart_type,
                chartData: payload.chart_data,
                explanation: payload.explanation,
                scenarioId: payload.scenario_id,
                streaming: false,
                status: null,
              }),
            onError: (detail) =>
              patch(assistantId, { content: detail, error: true, streaming: false, status: null }),
          },
          controller.signal
        );
      } catch (err) {
        const aborted =
          controller.signal.aborted ||
          (err instanceof Error && (err.name === "AbortError" || /aborted/i.test(err.message)));
        if (aborted) {
          // Keep whatever streamed so far; just stop. (If the message was
          // cleared by reset/load, patching a gone id is a harmless no-op.)
          patch(assistantId, { streaming: false, status: null });
        } else {
          const detail = err instanceof Error ? err.message : "Something went wrong";
          patch(assistantId, { content: detail, error: true, streaming: false, status: null });
        }
      } finally {
        controllerRef.current = null;
        setLoading(false);
      }
    },
    [loading, patch, appendDelta, appendTool, appendThinking, messages, conversationId]
  );

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    setMessages([]);
    setLoading(false);
    const id =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `c-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    persistId(id);
    setConversationId(id);
  }, []);

  const loadConversation = useCallback(async (id: string) => {
    if (!id) return;
    controllerRef.current?.abort();
    setLoading(false);
    try {
      const data = await clientApi.getConversation(id);
      const msgs: ChatMessageData[] = [];
      for (const t of data.turns ?? []) {
        if (!t || typeof t !== "object") continue; // best-effort: skip bad rows
        const q = String(t.question ?? "").trim();
        const a = String(t.answer ?? "").trim();
        if (q) msgs.push({ id: nextId(), role: "user", content: q });
        if (a || t.error) {
          msgs.push({
            id: nextId(),
            role: "assistant",
            content: a,
            error: !!t.error,
            tools: (t.tool_calls ?? [])
              .filter((tc) => tc && tc.name)
              .map((tc) => ({
                name: String(tc.name),
                label: String(tc.label ?? tc.name),
                args: (tc as { args?: unknown }).args,
              })),
            chartType: (t.chart_type as ChartType | null | undefined) ?? null,
            chartData: t.chart_data ?? null,
            explanation: (t.explanation as ChatExplanation | null | undefined) ?? null,
            scenarioId: t.scenario_id ?? null,
          });
        }
      }
      setMessages(msgs);
      setConversationId(id);
      persistId(id);
    } catch {
      // best-effort: if the conversation can't be loaded, start fresh with this id
      setMessages([]);
      setConversationId(id);
      persistId(id);
    }
  }, []);

  return { messages, loading, send, stop, reset, loadConversation, conversationId };
}
