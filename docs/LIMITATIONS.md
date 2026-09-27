# Limitations

Said plainly, not glossed over.

## Real data in, honest (and mixed) results out

Every input the backtest sees is real market data:

- **rToken price**: actual traded Bitget rToken prices — the close of each
  real 15-minute spot candle for `RTSLAUSDT`, `RNVDAUSDT`, `RAAPLUSDT`,
  `RAMZNUSDT`, `RMSFTUSDT` from Bitget's public market-data API
  (`scripts/fetch_rtoken_candles.py`, see `API_NOTES.md`). A bar is only
  observed at its close time, so no row can see a future price.
- **Cash close / next open**: real daily OHLCV of the underlying stocks
  (`bitget-mcp-server`). The close anchors the spread; the next open is
  carried only to grade the forecast after the fact — the signal never
  reads it.
- **Event dates**: real earnings dates (`bitget-mcp-server`
  `equity_calendar_earnings`) plus real FOMC/CPI dates.

Alignment check: the rToken print at 16:00 ET sits a median 0.01–0.02%
from the official cash close on every symbol, and every one of the 77
nights per symbol has a bar exactly at the 09:30 ET open.

**Earlier versions of this repo used a modeled after-hours path derived
from the realized next open.** That leaked the outcome into the input and
produced Sharpe 7–9 with near-zero drawdown. It was replaced with real
rToken candles; the numbers below are what the unchanged strategy
(same config, no retuning) does on real prices.

| Symbol | Trades | Sharpe | IS Sharpe (trades) | OOS Sharpe (trades) | OOS decay flag |
|---|---|---|---|---|---|
| rTSLA | 45 | 3.55 | 5.63 (33) | -1.46 (12) | yes |
| rNVDA | 53 | 2.96 | 3.73 (41) | 1.78 (12) | yes, barely (0.48x) |
| rAAPL | 9 | 3.69 | 4.53 (8) | n/a (1) | too few trades |
| rAMZN | 20 | 1.16 | 2.42 (14) | -3.67 (6) | yes |
| rMSFT | 18 | 1.01 | 1.08 (17) | n/a (1) | too few trades |

Costs: Bitget's published rToken spot fee, 0.10% per side (`takerFeeRate`
in the public symbols API, identical for all five pairs), plus
clip-dependent slippage. An earlier run used 6 bps per side — Bitget's
TSLAUSDT *futures* taker rate, not the rToken spot rate — which understated
costs; at 6 bps rNVDA's OOS ratio was 0.63x.

Read plainly:

- **The edge decays out of sample.** Only rNVDA stays profitable past
  the 2026-08-01 split, and even it falls just under the 0.5x reference.
  Summed across all five symbols, the 32 OOS trades lose about $100 on
  $5,000 tiers — roughly flat after costs.
- **Where it decays**: on rTSLA the "fade" branch won 24 of 30 trades in
  June–July but 2 of 10 in August–September, stopped out fast. Across
  all five symbols, typical nightly spikes were 25–40% smaller out of
  sample. rTokens
  launched in June 2026; a plausible (untested) explanation is that the
  young, thin book overreacted early and those overreactions shrank as
  liquidity arrived. That is a hypothesis, not a result.
- **Parameters were not tuned on this data.** Retuning the threshold/stop
  on the full window would make the OOS look better by construction —
  that is the overfitting the IS/OOS split exists to catch.
- **Short sample.** 77 nights per symbol; single-trade OOS Sharpes (rAAPL,
  rMSFT) are meaningless and shown as such. A Sortino of 0.00 with 0.00
  max drawdown (rAAPL) means *no losing days* in 9 trades, not a bad
  Sortino.
- **Fills are at the bar close price.** Real fills in a thin rToken book
  would be worse; see the cost-model and liquidity sections below.
- **USDT vs USD.** rTokens quote in USDT and the cash close is in USD; the
  USDT/USD basis (typically a few bps) is ignored.

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
(`mae_pct`, `directional_accuracy`) inherits the same short-sample caveats as the trading backtest above.

## Cost model is a simplification

`_cost_bps` in `seal/backtest.py` models total slippage as decaying with
`1/sqrt(clip_count)` — a standard simplification for impact reduction from
time-diversified execution, not a fitted market-impact model for Bitget's
actual rToken order book depth (no historical order-book data was
available to calibrate against).

## Thin rToken books

Real 15-minute bars show that some rToken pairs trade very little per bar
at times (a handful of bars have zero volume). A real traded price does
not mean the configured parent size ($5,000 tier) could have filled at it
— which is exactly the problem the Seal clip layer is meant to address,
but its cost model has not been calibrated against real order-book depth.
