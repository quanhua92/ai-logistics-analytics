"use client";

import { useId, useState } from "react";
import { type LucideIcon, TrendingDown, TrendingUp } from "lucide-react";

import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { DynamicChart } from "@/components/charts/dynamic-chart";
import type { KpiTrendPoint } from "@/lib/types";
import { cn } from "@/lib/utils";

export type KpiTone = "emerald" | "blue" | "amber" | "rose" | "violet" | "neutral";

const TONES: Record<KpiTone, string> = {
  emerald: "bg-emerald-500/10 text-emerald-600",
  blue: "bg-blue-500/10 text-blue-600",
  amber: "bg-amber-500/10 text-amber-600",
  rose: "bg-rose-500/10 text-rose-600",
  violet: "bg-violet-500/10 text-violet-600",
  neutral: "bg-muted text-muted-foreground",
};

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  icon?: LucideIcon;
  tone?: KpiTone;
  series?: KpiTrendPoint[];
  delta?: number | null;
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
  const [open, setOpen] = useState(false);
  const values = series?.map((p) => p.value) ?? [];
  const good = delta == null ? null : invertDelta ? delta < 0 : delta >= 0;
  const sparkStroke = good == null ? "#94a3b8" : good ? "#10b981" : "#f43f5e";
  const hasTrend = values.length > 1;

  const card = (
    <Card
      onClick={hasTrend ? () => setOpen(true) : undefined}
      onKeyDown={
        hasTrend
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setOpen(true);
              }
            }
          : undefined
      }
      role={hasTrend ? "button" : undefined}
      tabIndex={hasTrend ? 0 : undefined}
      className={cn(
        "shadow-card group gap-0 overflow-hidden px-4 py-3 transition-shadow duration-200 hover:shadow-card-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        hasTrend && "cursor-pointer"
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-1.5">
          {Icon ? (
            <div
              className={cn(
                "flex size-6 shrink-0 items-center justify-center rounded-md",
                TONES[tone]
              )}
            >
              <Icon className="size-3.5" />
            </div>
          ) : null}
          <span className="truncate text-xs font-medium text-muted-foreground">{label}</span>
        </div>
        {delta != null ? (
          <span
            className={cn(
              "inline-flex shrink-0 items-center gap-0.5 text-[11px] font-semibold",
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
      </div>

      <div className="mt-1.5 flex items-baseline gap-1.5">
        <div className="text-[22px] leading-none font-semibold tracking-tight tabular-nums">
          {value}
        </div>
        {hint ? (
          <span className="truncate text-[11px] text-muted-foreground">{hint}</span>
        ) : null}
      </div>

      {hasTrend ? (
        <div className="mt-2">
          <Sparkline values={values} stroke={sparkStroke} />
        </div>
      ) : null}
    </Card>
  );

  if (!hasTrend) return card;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {card}
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="text-lg">{label}</DialogTitle>
          <DialogDescription>
            Monthly trend · last {values.length} months
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-baseline gap-3">
          <div className="text-3xl font-semibold tracking-tight tabular-nums">{value}</div>
          {delta != null ? (
            <span
              className={cn(
                "inline-flex items-center gap-1 text-sm font-semibold",
                good ? "text-emerald-600" : "text-rose-600"
              )}
            >
              {delta >= 0 ? <TrendingUp className="size-4" /> : <TrendingDown className="size-4" />}
              {Math.abs(delta)}% vs last month
            </span>
          ) : null}
        </div>
        <div className="-mx-2">
          <DynamicChart
            chartType="area"
            data={(series ?? []).map((p) => ({ month: p.month, [label]: p.value }))}
            height={360}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Sparkline({ values, stroke }: { values: number[]; stroke: string }) {
  const id = useId();
  if (values.length < 2) return null;
  const w = 100;
  const h = 28;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - 3 - ((v - min) / range) * (h - 6);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const linePts = pts.join(" ");
  const areaPts = `${linePts} ${w},${h} 0,${h}`;
  const gid = `spark-${id}`;
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      aria-hidden
      className="h-9 w-full"
    >
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity={0.32} />
          <stop offset="100%" stopColor={stroke} stopOpacity={0.02} />
        </linearGradient>
      </defs>
      <polygon points={areaPts} fill={`url(#${gid})`} />
      <polyline
        points={linePts}
        fill="none"
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
