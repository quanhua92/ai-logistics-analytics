"use client";

import { useCallback, useRef, useState } from "react";

import { clientApi } from "@/lib/api";
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
}

let _seq = 0;
const nextId = () => `m${++_seq}`;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef(false);

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

  const send = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || loading) return;
      abortRef.current = false;

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
        await clientApi.chatStream(q, {
          onStatus: () => patch(assistantId, { status: "Thinking…" }),
          onTool: (label) => patch(assistantId, { status: label }),
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
    [loading, patch, appendDelta]
  );

  const reset = useCallback(() => {
    abortRef.current = true;
    setMessages([]);
    setLoading(false);
  }, []);

  return { messages, loading, send, reset };
}
