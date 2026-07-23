import type { LucideIcon } from "lucide-react";

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
}

export function KpiCard({ label, value, hint, icon: Icon, tone = "neutral" }: KpiCardProps) {
  return (
    <Card className="shadow-card gap-0 px-4 py-3.5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-xs font-medium text-muted-foreground">{label}</div>
          <div className="mt-1 text-[22px] leading-tight font-semibold tracking-tight tabular-nums">
            {value}
          </div>
          {hint ? (
            <div className="mt-0.5 truncate text-[11px] text-muted-foreground">{hint}</div>
          ) : null}
        </div>
        {Icon ? (
          <div
            className={cn(
              "flex size-8 shrink-0 items-center justify-center rounded-lg",
              TONES[tone]
            )}
          >
            <Icon className="size-4" />
          </div>
        ) : null}
      </div>
    </Card>
  );
}
