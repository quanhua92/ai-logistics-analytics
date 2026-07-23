"use client";

import { useEffect, useState } from "react";
import { Loader2, MessageSquare } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { clientApi, type ConversationSummary } from "@/lib/api";

function fmtTime(ts: string): string {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return "";
  const now = Date.now();
  const diff = (now - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString();
}

export function HistoryDialog({
  open,
  onOpenChange,
  onPick,
  currentId,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onPick: (id: string) => void;
  currentId?: string;
}) {
  const [list, setList] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch-on-open data loading
    setLoading(true);
    clientApi
      .listConversations()
      .then(setList)
      .catch(() => setList([]))
      .finally(() => setLoading(false));
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Conversation history</DialogTitle>
          <DialogDescription>Pick a past conversation to resume it.</DialogDescription>
        </DialogHeader>
        <div className="-mx-2 max-h-[60vh] overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-8 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" /> Loading…
            </div>
          ) : list.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">No conversations yet.</p>
          ) : (
            <ul className="space-y-1">
              {list.map((c) => (
                <li key={c.conversation_id}>
                  <button
                    type="button"
                    onClick={() => {
                      onPick(c.conversation_id);
                      onOpenChange(false);
                    }}
                    className={`flex w-full items-start gap-2.5 rounded-lg px-3 py-2 text-left transition-colors hover:bg-muted ${
                      c.conversation_id === currentId ? "bg-muted ring-1 ring-primary/30" : ""
                    }`}
                  >
                    <MessageSquare className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium">
                        {c.first_question || "(empty conversation)"}
                      </span>
                      <span className="block text-xs text-muted-foreground">
                        {c.turn_count} turn{c.turn_count === 1 ? "" : "s"} · {fmtTime(c.last_ts)}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
