import { TrendingUp } from "lucide-react";

import { ForecastView } from "@/components/forecast/forecast-view";
import { serverApi } from "@/lib/api";

export const revalidate = 60;
const DEFAULT_HORIZON = 4;

export default async function ForecastPage() {
  const categories = await serverApi.forecastCategories();
  const initial = await serverApi.forecast(categories[0], DEFAULT_HORIZON);

  return (
    <div className="space-y-5">
      <header className="space-y-1">
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
          <TrendingUp className="size-5 text-primary" />
          Demand forecasting
        </h1>
        <p className="text-sm text-muted-foreground">
          Project future monthly demand per category. Pure statistics — linear
          regression, moving average, and exponential smoothing. No AI involved.
        </p>
      </header>

      <ForecastView categories={categories} initial={initial} />
    </div>
  );
}
