import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "warning";
}

export function KpiCard({ label, value, hint, tone = "default" }: KpiCardProps) {
  return (
    <Card className="px-4 py-3">
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div
        className={cn(
          "mt-1 text-2xl font-semibold tracking-tight tabular-nums",
          tone === "warning" && "text-rose-600"
        )}
      >
        {value}
      </div>
      {hint ? (
        <div className="mt-0.5 text-xs text-muted-foreground">{hint}</div>
      ) : null}
    </Card>
  );
}
