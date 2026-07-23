"use client";

import { useState } from "react";
import { ChevronRight, Database, Filter, Lightbulb } from "lucide-react";

import type { ChatExplanation } from "@/lib/types";

export function ExplanationPanel({ explanation }: { explanation: ChatExplanation }) {
  const [open, setOpen] = useState(false);

  const filters = explanation.filters_used ?? [];
  const dims = explanation.dimensions ?? [];
  const summary = explanation.data_summary;
  const rec = explanation.recommendation;

  const hasBody =
    filters.length > 0 || dims.length > 0 || summary || rec || explanation.methodology;

  return (
    <div className="mt-3 overflow-hidden rounded-lg border bg-muted/30">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/50"
      >
        <ChevronRight
          className={`size-3.5 shrink-0 transition-transform ${open ? "rotate-90" : ""}`}
        />
        How this was calculated
      </button>

      {open && hasBody && (
        <div className="space-y-2.5 border-t px-3 py-2.5 text-xs">
          {explanation.metric && (
            <Row icon={<Database className="size-3.5" />} label="Metric">
              <span className="font-medium text-foreground">{explanation.metric}</span>
              {dims.length > 0 && (
                <span className="text-muted-foreground"> · by {dims.join(", ")}</span>
              )}
            </Row>
          )}
          {explanation.method && (
            <Row icon={<Database className="size-3.5" />} label="Method">
              {explanation.method}
            </Row>
          )}
          {filters.length > 0 && (
            <Row icon={<Filter className="size-3.5" />} label="Filters">
              {filters.map((f, i) => (
                <code key={i} className="rounded bg-background px-1 py-0.5 text-[11px]">
                  {f.field} {f.op} {String(f.value)}
                </code>
              ))}
            </Row>
          )}
          {summary && (
            <Row icon={<Database className="size-3.5" />} label="Data">
              {summary.row_count} rows
            </Row>
          )}
          {rec && (
            <Row icon={<Lightbulb className="size-3.5" />} label="Recommendation">
              {rec.note ?? "See forecast output"}
            </Row>
          )}
          {explanation.methodology && (
            <p className="pt-1 text-muted-foreground">{explanation.methodology}</p>
          )}
        </div>
      )}
    </div>
  );
}

function Row({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-2">
      <span className="mt-0.5 text-muted-foreground/70">{icon}</span>
      <div className="flex flex-1 flex-wrap items-center gap-x-1.5 gap-y-1">
        <span className="text-muted-foreground">{label}:</span>
        {children}
      </div>
    </div>
  );
}
