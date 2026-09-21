# SEAL

**Trade Bitget rTokens when US cash stocks are closed. Publish the rule. Seal the size.**

SEAL is a quantitative strategy for **Bitget AI Hackathon S2 — Alpha Factory**.

It trades **tokenized US stocks (rTokens) on Bitget** in the window when NYSE and Nasdaq are shut. The signal is public and reproducible. Live working size is split into small clips so a thin after-hours book cannot read the full order.

Track: **Alpha Factory** (Quantitative Strategies)  
Sub-theme: **After-Hours Information Pricing**  
Handbook: https://bitget-ai.gitbook.io/bitgetai_hackathons2  
Deadline: **21 September 2026, 23:59 UTC+8**

**Live**: [seal-alpha-factory.vercel.app](https://seal-alpha-factory.vercel.app) (dashboard) · [seal-backend-vxtk.onrender.com](https://seal-backend-vxtk.onrender.com) (API)

---

## What SEAL is

SEAL is not a wallet, not a lending protocol, and not a trading chatbot.

It is two layers on one book:

1. **Signal** — a rules-based after-hours signal: rToken vs last official cash close.  
2. **Seal** — the parent order is never sent as one print. It is clipped and jittered on Bitget.

AI (Qwen / Cursor) may write code and search parameters. It does **not** decide fills. The saved config is what you backtest and what judges replay.

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

One name. No add-ons in the same window. Hard notional cap, expressed as a **tier**, not a public dollar ticket.

### Execution (Seal)

1. Parent size comes from the signal and the tier cap.  
2. Parent is split into clips (for example 10–20% each).  
3. Clips go to Bitget with short random delays.  
4. Clipping stops if the spread is gone, the stop is hit, or cash is about to open.  
5. PnL and Sharpe are scored on the **parent**, not on each child.

**Hidden in live/paper logs:** residual size, clip count, jitter salt.  
**Public for judges:** rules, costs, parent equity curve, backtest metrics.

That is confidentiality here: **the after-hours book does not see full size.** It is not Attestcoin and not a confidential vault.

---

## How Bitget is integrated

Bitget is the market and the backtest host.

| Piece | Use |
|---|---|
| Bitget rToken | Only tradable instrument |
| Bitget price / last / mid | `spread` vs cash close |
| Bitget orders | Child clips (paper or live) |
| Bitget Playbook | Official Alpha Factory backtest path — parent rules, PnL, max DD, Sharpe |
| Bitget account | Optional paper/live execution of the same clips |

```
US cash close (anchor)
        ↓
Bitget rToken price (cash shut)
        ↓
Signal rules → parent side + tier
        ↓
Seal splitter → N clips + jitter
        ↓
Bitget Playbook fill model  and/or  Bitget orders
        ↓
parent report (Sharpe, Sortino, DD, turnover)
```

Run two Playbook (or local) backtests on the **same signal**:

- one-shot parent  
- clipped parent with extra spread / impact  

Seal is doing its job if clipped results stay inside your impact budget.

No Creditcoin. No Attestcoin. No CC3 mocks.

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
├── configs/
│   └── default.yaml         # rTSLA, real event dates, IS/OOS split
├── data/
│   ├── tsla_ohlcv_raw.json  # real TSLA OHLCV via bitget-mcp-server (committed)
│   ├── real_series.csv      # derived: real close/open + after-hours model
│   │                        #   (gitignored — rebuilt by build_real_dataset.py,
│   │                        #   including in CI, from the committed raw JSON)
│   └── sample_series.csv    # synthetic, standalone convenience generator for
│                             #   local exploration — NOT used by pytest or CI
├── reports/                 # generated, gitignored — see Quick start
│   ├── backtest_summary.md  # human-readable
│   ├── backtest_summary.json # structured, served by backend/
│   └── equity_curve.csv
├── scripts/
│   ├── run_backtest.py
│   ├── generate_sample_data.py
│   └── build_real_dataset.py
├── backend/                 # TS/Fastify — serves the backtest report +
│   │                        #   a live forecast endpoint (the reframe)
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

python scripts/run_backtest.py --config configs/default.yaml
```

`configs/default.yaml` already points at `data/real_series.csv` — real TSLA
closes/opens (via `bitget-mcp-server`) plus a documented after-hours price
model (see `docs/LIMITATIONS.md` before treating the headline Sharpe as a
validated real-world edge; it isn't one yet). `scripts/generate_sample_data.py`
regenerates a synthetic fallback used by CI/tests, and
`scripts/build_real_dataset.py` rebuilds `real_series.csv` from
`tsla_ohlcv_raw.json`.

Backtest must cover **at least 60 days** total and **at least 30 days out of
sample** — the default config's window (Jun 1–Sep 17, 2026, split Aug 1)
clears both with margin. See `docs/PLAYBOOK_PUBLISH.md` for publishing the
same strategy through Bitget Playbook's sandbox as a second, platform-
sanctioned record.

**Backend + frontend (serves the report, demos the reframe):**

```bash
pnpm install
pnpm --filter @seal/backend dev     # http://localhost:8787
pnpm --filter @seal/frontend dev    # http://localhost:3000
```

Requires `reports/backtest_summary.json` to exist first (produced by the
Python step above). Gate for CI/local: `pnpm lint && pnpm typecheck &&
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

- Built with **Claude Sonnet 5, via Claude Code** (the Qwen hackathon
  subsidy explicitly excludes Claude Code, so this isn't a Qwen build).
- Used to scaffold `signal.py` / `execution.py` / `backtest.py`, pull real
  TSLA price history via `bitget-mcp-server`, and design the metrics
  extensions (IS/OOS split, rolling Sharpe, cost-gap, forecast accuracy).
- Not used inside `backtest.py` to pick a trade's side or size at runtime —
  that's deterministic code (`seal/signal.py`, `seal/execution.py`), not a
  model call.

---

## Submission checklist (Alpha Factory)

- [ ] Form track: **Alpha Factory** · sub-theme: **After-Hours Information Pricing**  
- [ ] Project Description: this alpha, this user, these metrics  
- [ ] Public GitHub with this README  
- [ ] Runnable `scripts/run_backtest.py`  
- [ ] Backtest ≥ 60 days, OOS ≥ 30 days  
- [ ] LLM role field filled  
- [ ] X post with `#BitgetHackathon` and `@Bitget_AI` (not a bare retweet)  
- [ ] Links in **Submission Materials Link**, one per line, labeled  

Form: https://forms.gle/GyWZCMCPocgJdJon6  
Landing: https://www.bitget.com/activity-hub/hackathon

---

## What this is not

- Not a confidential RWA loan  
- Not Attestcoin / Creditcoin  
- Not Agentic Trading (the LLM is not the decision-maker)  
- Not an AI research desk  

Those were a different hackathon. SEAL is only: **Bitget rToken, cash closed, sealed clips, replayable parent backtest.**

---

## License

MIT

Backtest and paper trading only unless you send clips on Bitget with your own account and risk. Not financial advice.
