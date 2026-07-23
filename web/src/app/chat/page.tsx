"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowUp, Bot, Check, Copy, History, RotateCcw, Sparkles } from "lucide-react";

import { ChatMessage } from "@/components/chat/chat-message";
import { HistoryDialog } from "@/components/chat/history-dialog";
import { useChat } from "@/hooks/use-chat";
import { clientApi } from "@/lib/api";

function newId() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `c-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

const SUGGESTIONS = [
  "Which carrier has the highest delay rate?",
  "Show order volume trend over 2025",
  "What's the total revenue by region?",
  "Which months are worst for delays?",
  "Forecast demand for PAINT for the next 4 months",
  "Who are our top clients by revenue?",
];

export default function ChatPage() {
  const { messages, loading, send, loadConversation, conversationId } = useChat();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [input, setInput] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // The URL is the source of truth for which conversation is shown.
  // ?c=<id> loads/replays it. Bare /chat resumes the most recent conversation
  // (so you continue where you left off) or starts fresh if none exists.
  useEffect(() => {
    const c = searchParams.get("c");
    if (c) {
      void loadConversation(c);
      return;
    }
    void (async () => {
      try {
        const list = await clientApi.listConversations();
        const last = list[0]?.conversation_id;
        router.replace(`/chat?c=${last ?? newId()}`);
      } catch {
        router.replace(`/chat?c=${newId()}`);
      }
    })();
  }, [searchParams, router, loadConversation]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const submit = (text?: string) => {
    const value = (text ?? input).trim();
    if (!value || loading) return;
    send(value);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const onInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const empty = messages.length === 0;

  return (
    <div className="mx-auto flex h-[calc(100vh-3.5rem)] max-w-3xl flex-col">
      <header className="flex items-center justify-between px-1 pt-1">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <Sparkles className="size-4 text-primary" />
            Ask the data
          </h1>
          <p className="text-xs text-muted-foreground">
            Natural-language analytics — every answer is backed by live data.
          </p>
          {conversationId && <ConversationBadge id={conversationId} />}
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setHistoryOpen(true)}
            className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <History className="size-3.5" />
            History
          </button>
          {!empty && (
            <button
              type="button"
              onClick={() => router.push(`/chat?c=${newId()}`)}
              className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <RotateCcw className="size-3.5" />
              New chat
            </button>
          )}
        </div>
      </header>

      <HistoryDialog
        open={historyOpen}
        onOpenChange={setHistoryOpen}
        currentId={conversationId}
        onPick={(id) => router.push(`/chat?c=${id}`)}
      />

      <div className="flex-1 space-y-5 overflow-y-auto px-1 py-5">
        {empty ? (
          <EmptyState onPick={(q) => submit(q)} />
        ) : (
          messages.map((m) => <ChatMessage key={m.id} message={m} />)
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t bg-background/80 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-end gap-2 rounded-2xl border bg-card px-3 py-2 shadow-card focus-within:ring-2 focus-within:ring-ring/30">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={onInput}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Ask about orders, carriers, delays, revenue, forecasts…"
            className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-sm outline-none placeholder:text-muted-foreground/70"
          />
          <button
            type="button"
            onClick={() => submit()}
            disabled={!input.trim() || loading}
            className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-opacity disabled:opacity-40"
            aria-label="Send"
          >
            <ArrowUp className="size-4" />
          </button>
        </div>
        <p className="mt-1.5 px-1 text-center text-[11px] text-muted-foreground/70">
          Enter to send · Shift+Enter for a new line
        </p>
      </div>
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 text-center">
      <div className="mb-3 flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        <Bot className="size-6" />
      </div>
      <h2 className="text-base font-semibold">Ask anything about your logistics</h2>
      <p className="mb-6 mt-1 max-w-sm text-sm text-muted-foreground">
        Try one of these, or type your own question.
      </p>
      <div className="grid w-full max-w-xl grid-cols-1 gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onPick(q)}
            className="rounded-xl border bg-card px-3.5 py-2.5 text-left text-sm text-foreground shadow-card transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-card-hover"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function ConversationBadge({ id }: { id: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(id);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };
  return (
    <button
      type="button"
      onClick={copy}
      title={`Conversation ${id} — click to copy`}
      className="mt-1.5 inline-flex items-center gap-1.5 rounded-md border bg-muted/40 px-2 py-0.5 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
    >
      {copied ? <Check className="size-3 text-primary" /> : <Copy className="size-3" />}
      <span className="break-all">{id}</span>
    </button>
  );
}
