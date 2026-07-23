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
}

let _seq = 0;
const nextId = () => `m${++_seq}`;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef(false);

  const send = useCallback(async (question: string) => {
    const q = question.trim();
    if (!q || loading) return;
    abortRef.current = false;

    const userMsg: ChatMessageData = { id: nextId(), role: "user", content: q };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);

    try {
      const res = await clientApi.chat(q);
      if (abortRef.current) return;
      setMessages((m) => [
        ...m,
        {
          id: nextId(),
          role: "assistant",
          content: res.answer,
          chartType: res.chart_type,
          chartData: res.chart_data,
          explanation: res.explanation,
          scenarioId: res.scenario_id,
        },
      ]);
    } catch (err) {
      if (abortRef.current) return;
      const detail = err instanceof Error ? err.message : "Something went wrong";
      setMessages((m) => [
        ...m,
        { id: nextId(), role: "assistant", content: detail, error: true },
      ]);
    } finally {
      setLoading(false);
    }
  }, [loading]);

  const reset = useCallback(() => {
    abortRef.current = true;
    setMessages([]);
    setLoading(false);
  }, []);

  return { messages, loading, send, reset };
}
