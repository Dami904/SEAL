"use client";

import { useState } from "react";
import { Card, CardLabel } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fetchForecast, SUPPORTED_SYMBOLS, type ForecastResponse } from "@/lib/api";

const SYMBOL_LABELS: Record<string, string> = {
  rtsla: "rTSLA",
  rnvda: "rNVDA",
  raapl: "rAAPL",
  ramzn: "rAMZN",
  rmsft: "rMSFT",
};

export function ForecastForm() {
  const [symbol, setSymbol] = useState("rtsla");
  const [rtokenPrice, setRtokenPrice] = useState("340");
  const [cashClose, setCashClose] = useState("330");
  const [event, setEvent] = useState(false);
  const [result, setResult] = useState<ForecastResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const res = await fetchForecast({
      symbol: SYMBOL_LABELS[symbol] ?? symbol,
      rtokenPrice: Number(rtokenPrice),
      cashClose: Number(cashClose),
      event,
    });
    setLoading(false);
    if (!res) {
      setError("Backend not reachable — start it with `pnpm --filter @seal/backend dev`.");
      setResult(null);
      return;
    }
    setResult(res);
  }

  return (
    <Card>
      <CardLabel>Live forecast demo</CardLabel>
      <form onSubmit={onSubmit} className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <label className="col-span-2 sm:col-span-1">
          <span className="text-xs text-mist">Symbol</span>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="mt-1 w-full rounded-input border border-input bg-background px-3 py-2 text-sm text-snow"
          >
            {SUPPORTED_SYMBOLS.map((s) => (
              <option key={s} value={s}>
                {SYMBOL_LABELS[s]}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="text-xs text-mist">rToken price</span>
          <input
            type="number"
            step="0.01"
            value={rtokenPrice}
            onChange={(e) => setRtokenPrice(e.target.value)}
            className="mt-1 w-full rounded-input border border-input bg-background px-3 py-2 text-sm text-snow"
          />
        </label>
        <label>
          <span className="text-xs text-mist">Cash close</span>
          <input
            type="number"
            step="0.01"
            value={cashClose}
            onChange={(e) => setCashClose(e.target.value)}
            className="mt-1 w-full rounded-input border border-input bg-background px-3 py-2 text-sm text-snow"
          />
        </label>
        <label className="flex items-end gap-2 pb-2">
          <input
            type="checkbox"
            checked={event}
            onChange={(e) => setEvent(e.target.checked)}
            className="size-4"
          />
          <span className="text-xs text-mist">Scheduled event (FOMC/CPI/earnings)</span>
        </label>
        <div className="col-span-2 sm:col-span-4">
          <Button type="submit" disabled={loading}>
            {loading ? "Computing…" : "Get forecast"}
          </Button>
        </div>
      </form>

      {error && <p className="mt-4 text-sm text-danger">{error}</p>}

      {result && (
        <div className="mt-6 grid grid-cols-3 gap-6 border-t border-line pt-4">
          <div>
            <div className="text-xs uppercase tracking-wide text-mist">Spread</div>
            <div className="num mt-1 text-xl font-bold text-snow">
              {(result.spread * 100).toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-mist">Side</div>
            <div className="mt-1">
              {result.side ? (
                <Badge variant={result.side === "long" ? "good" : "destructive"}>
                  {result.side}
                </Badge>
              ) : (
                <Badge variant="secondary">no trade (below threshold)</Badge>
              )}
            </div>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-mist">Implied fair-value open</div>
            <div className="num mt-1 text-xl font-bold text-snow">
              ${result.impliedOpen.toFixed(2)}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
