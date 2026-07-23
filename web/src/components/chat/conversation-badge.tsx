"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

export function ConversationBadge({ id, className = "" }: { id: string; className?: string }) {
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
      className={`inline-flex max-w-[40vw] items-center gap-1.5 rounded-md border bg-muted/40 px-2 py-0.5 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground sm:max-w-none ${className}`}
    >
      {copied ? <Check className="size-3 shrink-0 text-primary" /> : <Copy className="size-3 shrink-0" />}
      <span className="truncate">{id}</span>
    </button>
  );
}
