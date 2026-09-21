import { PageHeader } from "@/components/layout/PageHeader";
import { MetricCard } from "@/components/MetricCard";
import { Card, CardLabel } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EquityCurveChart, RollingSharpeChart } from "@/components/charts";
import { fetchBacktestSummary } from "@/lib/api";

function pct(x: number, digits = 2) {
  return `${(x * 100).toFixed(digits)}%`;
}

export default async function BacktestPage() {
  const summary = await fetchBacktestSummary();

  if (!summary) {
    return (
      <div className="space-y-6">
        <PageHeader
          kicker="Alpha Factory · After-Hours Information Pricing"
          title="Backtest report"
          description="Trade Bitget rTokens when US cash stocks are closed. Sealed size, honest costs."
        />
        <Card>
          <p className="text-sm text-mist">
            Backend not reachable, or <code className="text-snow">reports/backtest_summary.json</code>{" "}
            doesn&apos;t exist yet. Run{" "}
            <code className="text-snow">python scripts/run_backtest.py --config configs/default.yaml</code>{" "}
            and start the backend (<code className="text-snow">pnpm --filter @seal/backend dev</code>).
          </p>
        </Card>
      </div>
    );
  }

  const { headline, in_sample_out_of_sample: split, rolling_30day_sharpe: rolling, one_shot_vs_clipped: gap } = summary;
  const decayWarning = split?.oos_decay_flag ?? false;

  return (
    <div className="space-y-8">
      <PageHeader
        kicker={`Alpha Factory · After-Hours Information Pricing · ${summary.symbol}`}
        title="Backtest report"
        description="Same signal. Sealed size. The rToken reprices while cash is shut; the parent order goes out as randomized clips so a thin after-hours book can't read the full size."
      />

      <p className="max-w-2xl text-xs leading-relaxed text-mist">
        These numbers are a backtest against a documented after-hours price model
        (real close/open, modeled intraday path) over a 75-trading-day window — see{" "}
        <code className="text-snow">docs/LIMITATIONS.md</code>. Short sample; treat as illustrative
        of the mechanism, not a validated real-world edge.
      </p>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <MetricCard label="Trades" value={String(headline.trade_count)} />
        <MetricCard
          label="Total PnL"
          value={`$${headline.total_pnl.toFixed(0)}`}
          tone={headline.total_pnl >= 0 ? "good" : "danger"}
        />
        <MetricCard label="Sharpe" value={headline.sharpe.toFixed(2)} />
        <MetricCard label="Sortino" value={headline.sortino.toFixed(2)} />
        <MetricCard
          label="Max drawdown"
          value={`$${headline.max_drawdown.toFixed(0)}`}
          tone="danger"
        />
        <MetricCard label="Turnover" value={`$${headline.turnover.toLocaleString()}`} />
      </div>

      <Card>
        <CardLabel>Equity curve</CardLabel>
        <div className="mt-3">
          <EquityCurveChart data={summary.equity_curve} />
        </div>
      </Card>

      {rolling.length > 0 && (
        <Card>
          <div className="flex items-center justify-between">
            <CardLabel>Rolling 30-day Sharpe</CardLabel>
            <span className="text-xs text-mist">dashed line = 0.5 reference</span>
          </div>
          <div className="mt-3">
            <RollingSharpeChart data={rolling} />
          </div>
        </Card>
      )}

      {split && (
        <Card>
          <div className="flex items-center justify-between">
            <CardLabel>In-sample / out-of-sample (split {split.split_date})</CardLabel>
            {decayWarning ? (
              <Badge variant="warn">OOS decay: below 0.5× IS reference</Badge>
            ) : (
              <Badge variant="good">OOS decay within reference</Badge>
            )}
          </div>
          <div className="mt-4 grid grid-cols-2 gap-6">
            <div>
              <div className="text-xs uppercase tracking-wide text-mist">In-sample</div>
              <div className="num mt-1 text-xl font-bold text-snow">
                Sharpe {split.in_sample.sharpe.toFixed(2)}
              </div>
              <div className="text-xs text-mist">{split.in_sample.trade_count} trades</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-mist">Out-of-sample</div>
              <div className="num mt-1 text-xl font-bold text-snow">
                Sharpe {split.out_of_sample.sharpe.toFixed(2)}
              </div>
              <div className="text-xs text-mist">{split.out_of_sample.trade_count} trades</div>
            </div>
          </div>
          {split.oos_decay_ratio !== null && (
            <p className="mt-3 text-xs text-mist">
              OOS/IS ratio: <span className="text-snow">{split.oos_decay_ratio.toFixed(2)}</span>
            </p>
          )}
        </Card>
      )}

      <Card>
        <CardLabel>One-shot vs. clipped execution</CardLabel>
        <p className="mt-1 text-xs text-mist">
          Same signal, sent as one print vs. the configured multi-clip Seal execution.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-6">
          <div>
            <div className="text-xs uppercase tracking-wide text-mist">One-shot</div>
            <div className="num mt-1 text-xl font-bold text-snow">
              ${gap.one_shot.total_pnl.toFixed(0)}
            </div>
            <div className="text-xs text-mist">Sharpe {gap.one_shot.sharpe.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-mist">Clipped (Seal)</div>
            <div className="num mt-1 text-xl font-bold text-good">
              ${gap.clipped.total_pnl.toFixed(0)}
            </div>
            <div className="text-xs text-mist">Sharpe {gap.clipped.sharpe.toFixed(2)}</div>
          </div>
        </div>
        <p className="mt-3 text-xs text-mist">
          Improvement from clipping:{" "}
          <span className="text-good">${gap.pnl_improvement.toFixed(0)}</span>
        </p>
      </Card>

      <Card>
        <CardLabel>Forecast accuracy (the reframe)</CardLabel>
        <p className="mt-1 text-xs text-mist">
          Same signal, exposed as a pre-open fair-value forecast — scored against the realized open.
        </p>
        <div className="mt-4 grid grid-cols-3 gap-6">
          <div>
            <div className="text-xs uppercase tracking-wide text-mist">Scored trades</div>
            <div className="num mt-1 text-xl font-bold text-snow">{headline.forecast.count}</div>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-mist">MAE</div>
            <div className="num mt-1 text-xl font-bold text-snow">
              {pct(headline.forecast.mae_pct)}
            </div>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-mist">Directional accuracy</div>
            <div className="num mt-1 text-xl font-bold text-snow">
              {headline.forecast.directional_accuracy !== null
                ? pct(headline.forecast.directional_accuracy, 0)
                : "n/a"}
            </div>
            <div className="text-xs text-mist">
              {headline.forecast.directional_count} directional (&quot;follow&quot;) calls
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
