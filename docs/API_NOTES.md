# API notes

Measured behavior of every external API this repo depends on for
execution, per CLAUDE.md — filled in before writing a client, not after.

## `bitget-mcp-server` (measured)

- **Install**: `claude mcp add bitget-mcp-server --transport http https://agent.bitget.com/mcp`
  — HTTP transport, no API key in the documented install.
- **Connectivity gotcha (hit this session)**: `agent.bitget.com` failed to
  resolve via a local ISP/router DNS resolver (query refused), while public
  resolvers (8.8.8.8, 1.1.1.1) resolved it fine to a live Cloudflare-fronted
  host. Not a Bitget outage — if this server won't connect, check DNS
  before assuming the service is down.
- **Discovery**: `guide()` lists categories (`equity`, `crypto`, `etf`,
  `news`, `sentiment`); `guide(category="equity")` lists entries.
- **Entry used**: `equity_price_historical` — `do_query(entry_id=
  "equity_price_historical", params={"symbol": "TSLA", "start_date":
  "2026-06-01", "end_date": "2026-09-17"})`. Returned real daily OHLCV
  (open/high/low/close/volume/vwap/transactions), provider `massive`,
  `data_tier: free`, synchronous response (~0.5s), no pagination needed for
  a 75-row range. Used to build `data/tsla_ohlcv_raw.json` →
  `data/real_series.csv` (see `scripts/build_real_dataset.py`).
- **What it does NOT cover**: Bitget's own rToken price feed. This server
  is US-stock/ETF cash-market data only (per the `equity` category). It
  does not give the tokenized rToken's own trading price.

## Bitget rToken price feed — NOT measured, blocks live wiring

No read-only, documented endpoint for Bitget's own rToken price was found
or tested this session. `rtoken_price` in `data/real_series.csv` is a
documented model (see `docs/LIMITATIONS.md`), not real tick data. Per
CLAUDE.md: do not write a live client against this feed until it has been
found, tested, and its failure modes (timeout meaning, rate limits, staleness
window) are mapped here first.

## Bitget rToken structure (verified via Bitget's own docs + web research, not the hackathon handbook)

- Issued by Reality Protocol, launched June 2026 ("Bitget Stocks 2.0").
  Each rToken is 1:1 backed by the real underlying stock (not synthetic).
  Custody: Alpaca. Independent proof-of-assets: The Network Firm.
- Naming: `r` + ticker (e.g. `rTSLA`, `rNVDA`, `rAAPL`), 500+ supported.
- On-chain support (Arbitrum, Morph) added Aug 19, 2026 — **mainnet only**,
  no rToken testnet exists anywhere in Bitget's documentation.

## Bitget Playbook / GetAgent Skill

- Install: `npx @bitget-ai/getagent-skill@latest install --client agent`.
- Requires a Playbook account login + a separate Playbook API key (not an
  exchange API key), bound in GetAgent Studio — a manual, account-bound
  step. See `docs/PLAYBOOK_PUBLISH.md` for the exact flow.
- Its own displayed backtest output: return, max drawdown, win rate, trade
  count, Sharpe. **Missing**: Sortino, turnover, IS/OOS split — the
  handbook's judging criteria score all of those, so Playbook's output
  alone is insufficient; this repo's own `seal/backtest.py` remains the
  primary source of the scored metrics.

## Sanctioned live-execution path (not implemented, noted for later)

Bitget Agent Hub's `--paper-trading` flag routes order execution to a
separate Demo environment with its own Demo API key — no real funds, not
mainnet. This is the only path CLAUDE.md's mainnet-safety rule would permit
for live paper trading, if ever added. Any such script must be named with
a `live:` or `deploy:` prefix per CLAUDE.md and is out of scope for this
submission.
