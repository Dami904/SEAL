# SEAL

**Trade Bitget rTokens when US cash stocks are closed. Publish the rule. Seal the size.**

SEAL is a quantitative strategy for **Bitget AI Hackathon S2 — Alpha Factory**.

It trades **tokenized US stocks (rTokens) on Bitget** in the window when NYSE and Nasdaq are shut. The signal is public and reproducible. Live working size is split into small clips so a thin after-hours book cannot read the full order.

Track: **Alpha Factory** (Quantitative Strategies)  
Sub-theme: **After-Hours Information Pricing**  
Handbook: https://bitget-ai.gitbook.io/bitgetai_hackathons2  
Deadline: **27 September 2026, submission window closes (UTC+8)**

**Live**: [seal-alpha-factory.vercel.app](https://seal-alpha-factory.vercel.app) (dashboard) · [seal-backend-vxtk.onrender.com](https://seal-backend-vxtk.onrender.com) (API)  
**Demo video**: [Watch the demo](https://youtu.be/b1XXQ2hNn6c)

---

## What SEAL is

SEAL is not a wallet, not a lending protocol, and not a trading chatbot.

It is two layers on one book:

1. **Signal** — a rules-based after-hours signal: rToken vs last official cash close.  
2. **Seal** — the parent order is never sent as one print. It is clipped and jittered on Bitget.

AI (Claude, via Claude Code) wrote and audited the code. It does **not** decide trades, and the strategy parameters were fixed, not searched. The saved config is what you backtest and what judges replay.

If the instrument is not a Bitget rToken, it is not this project.

---

## Problem

Cash US equities stop. Bitget rTokens do not.

Nights, weekends, and holidays still produce news: earnings after the bell, FOMC, CPI, geopolitics. The rToken can reprice immediately. The cash stock only moves at the next open.

Most strategies either:

- wait for the cash open and miss the rToken move, or  
- dump full size into a thin extended-hours book.

The second failure is the confidentiality problem. In a quiet rToken book, one large print tells the market **who is leaning and how hard**. It also burns the spread through slippage. You do not need a private chain to care about that. You need **quiet execution**.

---

## Solution

**Same signal. Sealed size.**

### Signal

At the US regular-hours close, store the official close of the underlying stock.

While cash is shut, read the Bitget rToken price:

```
spread = rToken / cash_close - 1
```

If `|spread|` clears the entry threshold and the session is after-hours or weekend:

- Scheduled event window (FOMC, CPI, named earnings) → trade **with** the move.  
- No event → **fade** the spike (empty-book overreaction).

Exit at next cash open, when the spread mean-reverts, or at a hard stop.

One position at a time. No add-ons in the same window. Hard notional cap per trade, expressed as a **tier** ($5,000 in the published backtests).

### Execution (Seal)

1. Parent size comes from the signal and the tier cap.  
2. Parent is split into clips (8 clips of 8–20% each in the published configs).  
3. Clips go to Bitget with short random delays.  
4. Clipping stops if the spread is gone, the stop is hit, or cash is about to open.  
5. PnL and Sharpe are scored on the **parent**, not on each child.

**Private in live execution (planned):** residual size, clip count, jitter salt.  
**Public for judges:** rules, costs, parent equity curve, backtest metrics.

That is confidentiality here: **the after-hours book does not see full size.**

---

## How Bitget is integrated

Bitget is the market and the data source.

| Piece | Use | Status |
|---|---|---|
| Bitget rToken spot pairs (`RTSLAUSDT`, `RNVDAUSDT`, `RAAPLUSDT`, `RAMZNUSDT`, `RMSFTUSDT`) | The only instruments traded | Used |
| Bitget public market API (`history-candles`, `public/symbols`) | Real 15-minute rToken prices while cash is shut; published fee (0.10%) and price/size precision | Used |
| `bitget-mcp-server` | Real official closes/opens and earnings dates of the underlying stocks | Used |
| Bitget orders (Agent Hub paper trading) | Sending the child clips live | Not built yet |
| Bitget Playbook (GetAgent) | Platform-hosted copy of the backtest | Package drafted, not published (see `docs/PLAYBOOK_PUBLISH.md`) |

```
US cash close (anchor)
        ↓
Bitget rToken price (cash shut)
        ↓
Signal rules → parent side + tier
        ↓
Seal splitter → N clips + jitter
        ↓
Backtest fill model (bar close + Bitget fee + clip-dependent slippage)
        ↓
parent report (Sharpe, Sortino, DD, turnover, IS/OOS, rolling Sharpe)
```

The backtest runs the **same signal** twice:

- one-shot parent  
- clipped parent  

Seal is doing its job if the clipped run costs less than the one-shot run (it does on all five symbols; see the results table).

---

## Repo

```
seal/
├── README.md
├── seal/                    # Python: signal + execution + backtest core
│   ├── data.py              # loads/validates the after-hours price series
│   ├── signal.py            # spread, event flag, parent side
│   ├── execution.py         # clip, jitter, cancel remaining
│   ├── backtest.py          # parent fills, costs, IS/OOS, rolling Sharpe,
│   │                        #   cost-gap, forecast accuracy
│   └── params.py
├── configs/                 # one config per symbol — real event dates, IS/OOS split
│   ├── default.yaml         # rTSLA (also the backend's default)
│   ├── rnvda.yaml, raapl.yaml, ramzn.yaml, rmsft.yaml
├── data/
│   ├── r{tsla,nvda,aapl,amzn,msft}_rtoken_15m_raw.json  # REAL Bitget rToken
│   │                        #   15m candles, public API (committed)
│   ├── {tsla,nvda,aapl,amzn,msft}_ohlcv_raw.json  # real cash OHLCV via
│   │                        #   bitget-mcp-server (committed)
│   ├── r{tsla,nvda,aapl,amzn,msft}_series.csv      # derived: real rToken
│   │                        #   prices while cash is shut, anchored to the
│   │                        #   real close (gitignored — rebuilt offline by
│   │                        #   build_real_dataset.py, incl. in CI)
│   └── sample_series.csv    # synthetic, standalone convenience generator for
│                             #   local exploration — NOT used by pytest or CI
├── reports/                 # generated, gitignored — see Quick start
│   └── r{tsla,nvda,aapl,amzn,msft}_summary.{md,json}, *_equity_curve.csv
├── scripts/
│   ├── run_backtest.py
│   ├── generate_sample_data.py
│   ├── fetch_rtoken_candles.py  # pulls real rToken candles (network, run once)
│   └── build_real_dataset.py  # --symbol <slug> or --all (offline)
├── backend/                 # TS/Fastify — serves the backtest report +
│   │                        #   a live pre-open fair-value forecast endpoint
│   ├── src/{signal.ts, forecast.ts, routes/, server.ts}
│   └── test/
├── frontend/                 # TS/Next.js — /backtest, /forecast
│   └── src/{app/, components/, lib/}
├── docs/
│   ├── API_NOTES.md
│   ├── LIMITATIONS.md
│   ├── THREAT_MODEL.md
│   └── PLAYBOOK_PUBLISH.md
└── .github/workflows/ci.yml # python job (pytest) + js job (lint/typecheck/test/build)
```

---

## Quick start

**Python core (signal / backtest):**

```bash
git clone <this-repo>
cd seal
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# optional, needs network — raw candles are already committed:
# python scripts/fetch_rtoken_candles.py
python scripts/build_real_dataset.py --all    # or --symbol rtsla for just one
python scripts/run_backtest.py --config configs/default.yaml
# also: configs/rnvda.yaml, raapl.yaml, ramzn.yaml, rmsft.yaml
```

Five symbols are backtested **independently** — `rTSLA`, `rNVDA`, `rAAPL`,
`rAMZN`, `rMSFT` — to show the signal generalizes beyond one stock, not a
correlated portfolio (see `docs/LIMITATIONS.md`). Each config points at its
own **real Bitget rToken 15-minute prices** (public market API) while cash
is shut, anchored to the real official close (`bitget-mcp-server`). Nothing
in the backtest input is modeled — read `docs/LIMITATIONS.md` before
treating any headline Sharpe as a validated real-world edge; none of them
are one yet.
`scripts/generate_sample_data.py` regenerates a synthetic fallback for local
exploration only (not used by CI/tests), and `scripts/build_real_dataset.py`
rebuilds each symbol's series from the committed raw rToken + OHLCV JSON.

### Results on real rToken prices (strategy parameters unchanged, not retuned)

| Symbol | Trades | Sharpe | Sortino | Max DD ($) | IS Sharpe | OOS Sharpe | Clip gain ($) |
|---|---|---|---|---|---|---|---|
| rTSLA | 45 | 3.55 | 6.61 | -239 | 5.63 | -1.46 ⚠ | 43.6 |
| rNVDA | 53 | 2.96 | 9.27 | -126 | 3.73 | 1.78 ⚠ (0.48×) | 51.4 |
| rAAPL | 9 | 3.69 | n/a (no losing day) | 0 | 4.53 | n/a (1 trade) | 8.7 |
| rAMZN | 20 | 1.16 | 1.20 | -193 | 2.42 | -3.67 ⚠ | 19.4 |
| rMSFT | 18 | 1.01 | 2.90 | -109 | 1.08 | n/a (1 trade) | 17.5 |

Window Jun 1–Sep 21, 2026 (77 nights/symbol), IS/OOS split Aug 1. Costs
use Bitget's published rToken spot fee (0.10% per side, from the public
symbols API) plus clip-dependent slippage.
⚠ = OOS Sharpe < 0.5× IS (the handbook's decay reference). Positive in
sample on all five; out of sample only rNVDA stays profitable (and sits
just under the 0.5× line) — the fade edge shrank sharply after the rToken
launch month. We report that rather than retune on the full window.
Details: `docs/LIMITATIONS.md`.

Backtest must cover **at least 60 days** total and **at least 30 days out of
sample** — the default config's window (Jun 1–Sep 21, 2026, split Aug 1)
clears both with margin.

**Backend + frontend (serves the reports, demos the pre-open forecast):**

```bash
pnpm install
pnpm --filter @seal/backend dev     # http://localhost:8787
pnpm --filter @seal/frontend dev    # http://localhost:3000
```

The backend serves `reports/{symbol}_summary.json` from the Python step
above when present, and otherwise falls back to the committed snapshots in
`backend/seed/`. Gate for CI/local: `pnpm lint && pnpm typecheck &&
pnpm test && pnpm build` from the repo root.

---

## Metrics to publish

- Period PnL  
- Sharpe, Sortino  
- Max drawdown  
- Turnover  
- IS Sharpe vs OOS Sharpe  
- Rolling 30-day Sharpe  
- One-shot vs clipped cost gap  

Judges watch OOS decay (warning if OOS Sharpe &lt; 0.5× IS). Label paper trading separately from backtest.

---

## Target user

A trader who already uses Bitget rTokens and needs a **closed-market rule** that does not dump full size into the night book.

Not “all traders.” Not a research chatbot.

---

## Role of the LLM

- Built with **Claude Sonnet 5 and Claude Opus 5.5, via Claude Code** (no
  Qwen credits used).
- Used to write the Python engine, data pipeline, backend, frontend, tests
  and CI; pull real stock prices and earnings dates via `bitget-mcp-server`
  and real rToken candles and fees via Bitget's public API; and design the
  metrics (IS/OOS split, rolling Sharpe, cost-gap, forecast accuracy).
- Used to audit the work: it found and removed a lookahead leak in an early
  modeled dataset and corrected the fee to Bitget's published rToken spot
  rate.
- Not used inside `backtest.py` to pick a trade's side or size at runtime —
  that's deterministic code (`seal/signal.py`, `seal/execution.py`), not a
  model call.

---

## Submission checklist (Alpha Factory) — submitted

- [x] Form track: **Alpha Factory** · sub-theme: **After-Hours Information Pricing**  
- [x] Project Description: this alpha, this user, these metrics  
- [x] Public GitHub with this README  
- [x] Runnable `scripts/run_backtest.py`  
- [x] Backtest ≥ 60 days, OOS ≥ 30 days  
- [x] LLM role field filled  
- [x] X post with `#BitgetHackathon` and `@Bitget_AI`  
- [x] Links in **Submission Materials Link**, one per line, labeled  
- [x] Demo video  

Form: https://forms.gle/GyWZCMCPocgJdJon6  
Landing: https://www.bitget.com/activity-hub/hackathon

---

## License

MIT

Backtest only: nothing in this repo places orders. Not financial advice.
