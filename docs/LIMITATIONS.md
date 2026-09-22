# Limitations

Said plainly, not glossed over.

## The backtest's edge is not validated, and the headline Sharpe should not be read as a real-world expectation

The Sharpe/Sortino numbers in `reports/backtest_summary.md` come from a
77-trading-day window against a synthetic after-hours rToken price path
(see below). Two independent reasons the absolute numbers are optimistic:

- **Short sample.** 77 trading days is a very short backtest. Sharpe
  estimates from short windows are statistically noisy and routinely
  overstate the true long-run Sharpe — this is true of any strategy, not
  specific to SEAL.
- **Modeled rToken path.** The after-hours rToken price between the real
  close and the real next-day open (see below) is a documented model
  calibrated to plausible but arbitrary parameters, not fit to any real
  historical Bitget rToken tick data (none was accessible to us — see
  `API_NOTES.md`). The model was deliberately built to avoid a regression-
  to-the-mean artifact (an earlier version let "fade" trades win mostly by
  statistical coincidence, not real economics — fixed, see git history of
  `scripts/build_real_dataset.py`), but it has not been validated against
  real rToken market microstructure, and no attempt was made to tune it to
  produce a "nicer" Sharpe — that would be less honest, not more.

**What is real**: the underlying `cash_close` and `next_cash_open` values
are real daily OHLCV (fetched via `bitget-mcp-server`) for every symbol,
and each symbol's `event_dates` (its own real earnings date, from
`bitget-mcp-server`'s `equity_calendar_earnings`, plus real FOMC/CPI dates
that apply macro-wide) are real, verified calendar dates, not fabricated.
The trading P&L and forecast-accuracy metrics are graded against those real
outcomes. What's modeled is only the intermediate after-hours path the
strategy would have observed — see `scripts/build_real_dataset.py`.

**Before treating these numbers as a submission claim of edge**: re-run
against a longer real dataset and, ideally, real Bitget rToken historical
prices once accessible (see `API_NOTES.md` for what's missing), or validate
via Bitget Playbook's own backtest.

## Five symbols, independently — not a portfolio

`rTSLA`, `rNVDA`, `rAAPL`, `rAMZN`, `rMSFT` are each backtested
independently (`configs/{symbol}.yaml`, one report per symbol) to show the
signal generalizes beyond a single stock, not just curve-fit to one
earnings gap. This is **not** a correlated multi-symbol portfolio: there's
no shared position sizing, no cross-symbol risk limit, and no aggregate
drawdown across symbols traded simultaneously — each report stands alone.
Adding real portfolio-level logic (correlation-aware sizing, an aggregate
risk budget) is a materially bigger build than adding another independent
symbol and hasn't been done.

## No live execution

`seal/backtest.py` simulates fills; nothing in this repo places a real or
paper order. See `docs/API_NOTES.md` for the sanctioned path (Bitget Agent
Hub `--paper-trading`) if that's added later.

## Forecast is a point estimate, not a calibrated distribution

The pre-open fair-value forecast (`forecast_price` on each `Trade`, scored
in `BacktestResult.forecast_accuracy()`) is a single point estimate derived
from the same spread/event logic as the trade signal. It is not a
calibrated probability distribution over possible opens, and its accuracy
(`mae_pct`, `directional_accuracy`) inherits the same short-sample and
modeled-path caveats as the trading backtest above.

## Cost model is a simplification

`_cost_bps` in `seal/backtest.py` models total slippage as decaying with
`1/sqrt(clip_count)` — a standard simplification for impact reduction from
time-diversified execution, not a fitted market-impact model for Bitget's
actual rToken order book depth (no historical order-book data was
available to calibrate against).
