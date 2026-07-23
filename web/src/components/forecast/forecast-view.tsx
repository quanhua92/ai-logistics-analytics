"use client";

import { useState } from "react";
import { Boxes, Loader2, PackageCheck, Sigma, TrendingUp } from "lucide-react";

import { ForecastChart } from "@/components/forecast/forecast-chart";
import { clientApi } from "@/lib/api";
import type { ForecastResponse } from "@/lib/types";

export function ForecastView({
  categories,
  initial,
}: {
  categories: string[];
  initial: ForecastResponse;
}) {
  const [category, setCategory] = useState(initial.category);
  const [horizon, setHorizon] = useState(initial.horizon_months);
  const [data, setData] = useState(initial);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(cat: string, h: number) {
    setLoading(true);
    setError(null);
    try {
      setData(await clientApi.forecast(cat, h));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load forecast");
    } finally {
      setLoading(false);
    }
  }

  const onCategory = (v: string) => {
    setCategory(v);
    void load(v, horizon);
  };
  const onHorizon = (v: number) => {
    setHorizon(v);
    void load(category, v);
  };

  return (
    <div className="space-y-5">
      {/* Controls */}
      <div className="flex flex-wrap items-end gap-4 rounded-xl border bg-card p-4 shadow-card">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Category
          </span>
          <select
            value={category}
            onChange={(e) => onCategory(e.target.value)}
            className="h-9 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring/30"
          >
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="flex min-w-[200px] flex-1 flex-col gap-1">
          <span className="flex items-center justify-between text-xs font-medium uppercase tracking-wide text-muted-foreground">
            <span>Horizon</span>
            <span className="tabular-nums text-foreground">{horizon} month{horizon === 1 ? "" : "s"}</span>
          </span>
          <input
            type="range"
            min={1}
            max={12}
            value={horizon}
            onChange={(e) => onHorizon(Number(e.target.value))}
            className="h-9 w-full accent-primary"
          />
        </label>
      </div>

      {/* Chart */}
      <div className="rounded-xl border bg-card p-4 shadow-card">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold">
            {data.category} — demand forecast
          </h2>
          {loading && (
            <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin" /> Updating…
            </span>
          )}
        </div>
        <div className={loading ? "opacity-50 transition-opacity" : "transition-opacity"}>
          <ForecastChart data={data} />
        </div>
        {error && (
          <p className="mt-2 text-sm text-destructive">{error}</p>
        )}
      </div>

      {/* Recommendation */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-primary/5 p-4 shadow-card sm:col-span-1">
          <div className="flex items-center gap-2 text-primary">
            <PackageCheck className="size-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">
              Recommendation
            </span>
          </div>
          <div className="mt-3 text-3xl font-bold tabular-nums">
            {data.recommendation.safety_stock_units}
            <span className="ml-1 text-sm font-normal text-muted-foreground">units</span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{data.recommendation.note}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            Peak forecast:{" "}
            <span className="font-medium text-foreground tabular-nums">
              {data.recommendation.peak_forecast_units} units
            </span>
          </p>
        </div>

        <div className="rounded-xl border bg-card p-4 shadow-card sm:col-span-2">
          <div className="flex items-center gap-2 text-muted-foreground">
            <TrendingUp className="size-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Readiness</span>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-3">
            <Stat icon={<Sigma className="size-3.5" />} label="Mean / mo" value={data.readiness.mean_monthly_quantity} />
            <Stat icon={<Sigma className="size-3.5" />} label="Std dev" value={data.readiness.std_dev} />
            <Stat icon={<Boxes className="size-3.5" />} label="Data points" value={data.readiness.data_points} />
          </div>
          <p className="mt-3 border-t pt-2 text-xs leading-relaxed text-muted-foreground">
            {data.methodology}
          </p>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div>
      <div className="flex items-center gap-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {icon}
        {label}
      </div>
      <div className="mt-0.5 text-xl font-semibold tabular-nums">{value}</div>
    </div>
  );
}
