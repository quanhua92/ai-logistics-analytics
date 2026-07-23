"use client";

import ReactMarkdown from "react-markdown";
import { Bot, User } from "lucide-react";

import { ChartRenderer } from "@/components/charts/chart-renderer";
import { ExplanationPanel } from "@/components/chat/explanation-panel";
import type { ChatMessageData } from "@/hooks/use-chat";

export function ChatMessage({ message }: { message: ChatMessageData }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="flex max-w-[85%] items-start gap-2.5">
          <div className="rounded-2xl rounded-tr-sm bg-primary px-3.5 py-2 text-sm text-primary-foreground">
            {message.content}
          </div>
          <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <User className="size-3.5" />
          </div>
        </div>
      </div>
    );
  }

  const hasChart = message.chartData && message.chartData.length > 0 && message.chartType;

  return (
    <div className="flex justify-start">
      <div className="flex max-w-[92%] items-start gap-2.5">
        <div
          className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full ${
            message.error ? "bg-destructive/10 text-destructive" : "bg-muted text-muted-foreground"
          }`}
        >
          <Bot className="size-3.5" />
        </div>
        <div className="min-w-0 flex-1 space-y-2">
          {message.error ? (
            <p className="rounded-2xl rounded-tl-sm border border-destructive/30 bg-destructive/5 px-3.5 py-2 text-sm text-destructive">
              {message.content}
            </p>
          ) : (
            <div className="prose-chat rounded-2xl rounded-tl-sm border bg-card px-3.5 py-2.5 text-sm leading-relaxed shadow-card">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}

          {hasChart && (
            <div className="rounded-2xl border bg-card p-3 shadow-card">
              <ChartRenderer chartType={message.chartType!} data={message.chartData!} height={240} />
            </div>
          )}

          {!message.error && message.explanation && (
            <ExplanationPanel explanation={message.explanation} />
          )}
        </div>
      </div>
    </div>
  );
}
