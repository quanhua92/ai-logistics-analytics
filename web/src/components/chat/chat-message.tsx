"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, ChevronRight, Loader2, User, Wrench } from "lucide-react";

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

  // Render the chart card only for visual chart types. "table" is skipped
  // because react-markdown already renders the model's markdown table — showing
  // both would duplicate the data.
  const hasChart =
    !!message.chartData &&
    message.chartData.length > 0 &&
    !!message.chartType &&
    message.chartType !== "table";
  // Whitespace-only content (e.g. a leading newline token) counts as "no content"
  // so the Thinking… spinner stays until real text arrives — otherwise an empty
  // card flashes while the model is still composing.
  const hasContent = !!message.content && message.content.trim().length > 0;
  const showSpinner = !!message.streaming && !hasContent;
  const hasTools = !!message.tools && message.tools.length > 0;

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
          {hasTools && (
            <div className="flex flex-wrap gap-1.5">
              {message.tools!.map((t, i) => (
                <details key={i} className="group">
                  <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 rounded-full border bg-muted/40 px-2.5 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground [&::-webkit-details-marker]:hidden">
                    <Wrench className="size-3 shrink-0" />
                    {t.label}
                    <ChevronRight className="size-3 shrink-0 text-muted-foreground/60 transition-transform group-open:rotate-90" />
                  </summary>
                  <div className="mt-1 max-w-[80vw] overflow-x-auto rounded-md border bg-popover px-2.5 py-1.5 text-[10px] shadow-sm sm:max-w-md">
                    <div className="mb-0.5 font-mono text-[9px] uppercase tracking-wide text-muted-foreground/70">
                      {t.name}
                    </div>
                    <pre className="whitespace-pre-wrap break-all font-mono leading-snug text-muted-foreground">
                      {JSON.stringify(t.args ?? {}, null, 2)}
                    </pre>
                  </div>
                </details>
              ))}
            </div>
          )}

          {message.error ? (
            <p className="rounded-2xl rounded-tl-sm border border-destructive/30 bg-destructive/5 px-3.5 py-2 text-sm text-destructive">
              {message.content}
            </p>
          ) : hasContent ? (
            <div className="prose-chat rounded-2xl rounded-tl-sm border bg-card px-3.5 py-2.5 text-sm leading-relaxed shadow-card">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Wrap tables so wide ones scroll horizontally instead of
                  // overflowing the chat card.
                  table: (props) => (
                    <div className="overflow-x-auto">
                      <table {...props} />
                    </div>
                  ),
                  // Charts render via tool results, not markdown. Suppress any
                  // hallucinated image so it can't show a broken icon.
                  img: () => null,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          ) : null}

          {showSpinner && (
            <div className="inline-flex items-center gap-2 rounded-2xl rounded-tl-sm border bg-card px-3.5 py-2.5 text-sm text-muted-foreground shadow-card">
              <Loader2 className="size-3.5 animate-spin text-primary" />
              <span>Thinking…</span>
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
