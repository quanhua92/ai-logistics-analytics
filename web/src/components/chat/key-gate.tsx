"use client";

import { useState } from "react";
import { Eye, EyeOff, Lock } from "lucide-react";

export function KeyGate({
  onUnlock,
  error,
}: {
  onUnlock: (key: string) => void;
  error?: string | null;
}) {
  const [key, setKey] = useState("");
  const [show, setShow] = useState(false);
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const v = key.trim();
    if (!v) return;
    onUnlock(v);
  };
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-sm flex-col justify-center">
      <form onSubmit={submit} className="rounded-2xl border bg-card p-6 shadow-card">
        <div className="mb-3 flex size-10 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Lock className="size-5" />
        </div>
        <h2 className="text-lg font-semibold">Access key required</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter the chat access key to continue.
        </p>
        {error && (
          <p className="mt-3 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
            {error}
          </p>
        )}
        <div className="relative mt-4">
          <input
            type={show ? "text" : "password"}
            value={key}
            onChange={(e) => setKey(e.target.value)}
            autoFocus
            autoComplete="off"
            placeholder="Access key"
            className="h-10 w-full rounded-lg border bg-background px-3 pr-10 text-sm outline-none focus:ring-2 focus:ring-ring/30"
          />
          <button
            type="button"
            onClick={() => setShow((s) => !s)}
            tabIndex={-1}
            aria-label={show ? "Hide access key" : "Show access key"}
            className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-muted-foreground transition-colors hover:text-foreground"
          >
            {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
          </button>
        </div>
        <button
          type="submit"
          disabled={!key.trim()}
          className="mt-3 h-10 w-full rounded-lg bg-primary text-sm font-medium text-primary-foreground transition-opacity disabled:opacity-40"
        >
          Unlock
        </button>
        <p className="mt-4 rounded-md bg-muted/50 px-3 py-2 text-[11px] leading-relaxed text-muted-foreground">
          <strong className="text-foreground">Prototype access.</strong> This shared key is for the
          demo only — real deployment requires proper user authentication. Don&apos;t have a key?{" "}
          <a
            href="mailto:quanhua92@gmail.com"
            className="font-medium text-foreground underline underline-offset-2 hover:text-primary"
          >
            quanhua92@gmail.com
          </a>
          .
        </p>
      </form>
    </div>
  );
}
