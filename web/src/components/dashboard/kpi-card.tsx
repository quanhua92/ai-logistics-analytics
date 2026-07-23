import type { LucideIcon } from "lucide-react";
import { TrendingDown, TrendingUp } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type KpiTone = "emerald" | "blue" | "amber" | "rose" | "violet" | "neutral";

const TONES: Record<KpiTone, string> = {
  emerald: "bg-primary/10 text-primary",
  blue: "bg-sky-100 text-sky-700",
  amber: "bg-amber-100 text-amber-700",
  rose: "bg-rose-100 text-rose-700",
  violet: "bg-violet-100 text-violet-700",
  neutral: "bg-muted text-muted-foreground",
};

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  icon?: LucideIcon;
  tone?: KpiTone;
  series?: number[];
  delta?: number | null;
  /** true when a falling value is good (e.g. delayed, avg delivery) */
  invertDelta?: boolean;
}

export function KpiCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "neutral",
  series,
  delta = null,
  invertDelta = false,
}: KpiCardProps) {
  const good = delta == null ? null : invertDelta ? delta < 0 : delta >= 0;
  const sparkStroke =
    good == null ? "#94a3b8" : good ? "#10b981" : "#f43f5e";

  return (
    <Card className="shadow-card transition-shadow duration-200 gap-0 px-4 py-3.5 hover:shadow-card-hover">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-xs font-medium text-muted-foreground">{label}</div>
          <div className="mt-1 text-[22px] leading-tight font-semibold tracking-tight tabular-nums">
            {value}
          </div>
          <div className="mt-0.5 flex items-center gap-2">
            {delta != null ? (
              <span
                className={cn(
                  "inline-flex items-center gap-0.5 text-[11px] font-semibold",
                  good ? "text-emerald-600" : "text-rose-600"
                )}
              >
                {delta >= 0 ? (
                  <TrendingUp className="size-3" />
                ) : (
                  <TrendingDown className="size-3" />
                )}
                {Math.abs(delta)}%
              </span>
            ) : null}
            {hint ? (
              <span className="truncate text-[11px] text-muted-foreground">{hint}</span>
            ) : null}
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1.5">
          {Icon ? (
            <div
              className={cn(
                "flex size-8 items-center justify-center rounded-lg",
                TONES[tone]
              )}
            >
              <Icon className="size-4" />
            </div>
          ) : null}
          {series && series.length > 1 ? (
            <Sparkline values={series} stroke={sparkStroke} />
          ) : null}
        </div>
      </div>
    </Card>
  );
}

function Sparkline({ values, stroke }: { values: number[]; stroke: string }) {
  const w = 64;
  const h = 22;
  const pad = 2;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values
    .map((v, i) => {
      const x = pad + (i / (values.length - 1)) * (w - 2 * pad);
      const y = h - pad - ((v - min) / range) * (h - 2 * pad);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} aria-hidden className="overflow-visible">
      <polyline
        points={pts}
        fill="none"
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
