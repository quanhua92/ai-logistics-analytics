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
  tools?: { name: string; label: string }[];
}

const STORAGE_KEY = "logistics.chat.conversationId";

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
  const abortRef = useRef(false);

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

  const appendTool = useCallback((id: string, name: string, label: string) => {
    setMessages((m) =>
      m.map((msg) =>
        msg.id === id
          ? { ...msg, tools: [...(msg.tools ?? []), { name, label }], status: label }
          : msg
      )
    );
  }, []);

  const send = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || loading) return;
      abortRef.current = false;

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

      try {
        await clientApi.chatStream(q, history, conversationId, {
          onStatus: () => patch(assistantId, { status: "Thinking…" }),
          onTool: (name, label) => appendTool(assistantId, name, label),
          onToken: (delta) => appendDelta(assistantId, delta),
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
        });
      } catch (err) {
        if (abortRef.current) return;
        const detail = err instanceof Error ? err.message : "Something went wrong";
        patch(assistantId, { content: detail, error: true, streaming: false, status: null });
      } finally {
        setLoading(false);
      }
    },
    [loading, patch, appendDelta, appendTool, messages, conversationId]
  );

  const reset = useCallback(() => {
    abortRef.current = true;
    setMessages([]);
    setLoading(false);
    const id =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `c-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    persistId(id);
    setConversationId(id);
  }, []);

  return { messages, loading, send, reset, conversationId };
}
