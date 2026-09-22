import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardLabel } from "@/components/ui/card";
import { ForecastForm } from "./ForecastForm";
import { SymbolSwitcher } from "@/components/SymbolSwitcher";
import { fetchBacktestSummary, SUPPORTED_SYMBOLS, type SupportedSymbol } from "@/lib/api";

function pct(x: number, digits = 2) {
  return `${(x * 100).toFixed(digits)}%`;
}

function parseSymbol(raw: string | string[] | undefined): SupportedSymbol {
  const s = (Array.isArray(raw) ? raw[0] : raw)?.toLowerCase();
  return (SUPPORTED_SYMBOLS as readonly string[]).includes(s ?? "") ? (s as SupportedSymbol) : "rtsla";
}

export default async function ForecastPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string | string[] }>;
}) {
  const symbol = parseSymbol((await searchParams).symbol);
  const summary = await fetchBacktestSummary(symbol);
  const forecast = summary?.headline.forecast;

  return (
    <div className="space-y-8">
      <PageHeader
        kicker="The reframe"
        title="Pre-open fair-value forecast"
        description="Before the real market opens, the tokenized twin already indicates roughly where the stock will open. Same spread/event mechanism as the trading signal — pointed outward as a checkable forecast instead of only a trade decision."
      />

      <ForecastForm />

      <Card>
        <div className="flex items-center justify-between gap-4">
          <CardLabel>Backtested forecast accuracy</CardLabel>
          <SymbolSwitcher basePath="/forecast" active={symbol} />
        </div>
        <p className="mt-1 text-xs text-mist">
          Every entry in the backtest is a forecast, scored against the realized next-day open.
        </p>
        {forecast ? (
          <div className="mt-4 grid grid-cols-3 gap-6">
            <div>
              <div className="text-xs uppercase tracking-wide text-mist">Scored</div>
              <div className="num mt-1 text-xl font-bold text-snow">{forecast.count}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-mist">MAE</div>
              <div className="num mt-1 text-xl font-bold text-snow">{pct(forecast.mae_pct)}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-mist">Directional accuracy</div>
              <div className="num mt-1 text-xl font-bold text-snow">
                {forecast.directional_accuracy !== null ? pct(forecast.directional_accuracy, 0) : "n/a"}
              </div>
              <div className="text-xs text-mist">{forecast.directional_count} directional calls</div>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-sm text-mist">
            Backend not reachable, or the backtest hasn&apos;t been run yet.
          </p>
        )}
      </Card>
    </div>
  );
}
