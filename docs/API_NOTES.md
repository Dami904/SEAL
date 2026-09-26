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
- **Entries used**:
  - `equity_price_historical` — `do_query(entry_id="equity_price_historical",
    params={"symbol": "TSLA", "start_date": "2026-06-01", "end_date":
    "2026-09-17"})`. Returned real daily OHLCV (open/high/low/close/volume/
    vwap/transactions), provider `massive`, `data_tier: free`, synchronous
    (~0.5s), no pagination needed for a 75-row range. Confirmed working for
    TSLA, NVDA, AAPL, AMZN, MSFT — not a narrow whitelist, standard
    US-listed tickers broadly. Used to build `data/{symbol}_ohlcv_raw.json`
    → `data/{symbol}_series.csv` (see `scripts/build_real_dataset.py`).
  - `equity_calendar_earnings` — `do_query(entry_id="equity_calendar_earnings",
    params={"symbol": "NVDA", "start_date": ..., "end_date": ...})`. Returns
    real, verified earnings report dates directly (provider `finnhub`) —
    used instead of manual web search once discovered. This is what sourced
    each symbol's real event date in `configs/{symbol}.yaml`.
- **What it does NOT cover**: Bitget's own rToken price feed. This server
  is US-stock/ETF cash-market data only (per the `equity` category). It
  does not give the tokenized rToken's own trading price.

## Bitget rToken price feed — public spot candles (measured)

rTokens are listed as ordinary Bitget spot pairs: `RTSLAUSDT`, `RNVDAUSDT`,
`RAAPLUSDT`, `RAMZNUSDT`, `RMSFTUSDT` (all `status: online` in
`GET https://api.bitget.com/api/v2/spot/public/symbols`). Their historical
candles come from Bitget's **public, keyless** market-data API, and they are
the source of every `rtoken_price` in the backtest.

- **Endpoint**: `GET /api/v2/spot/market/history-candles?symbol=RTSLAUSDT&granularity=15min&endTime=<ms>&limit=200`.
- **Row shape**: `[ts, open, high, low, close, baseVol, usdtVol, quoteVol]`,
  all strings; `ts` is the bar **open** time in ms UTC. The close is only
  known at `ts + 15min`, so that is when the backtest observes it.
- **Pagination**: max 200 bars per call, newest first; page backward by
  setting `endTime` to the oldest `ts` returned. `scripts/fetch_rtoken_candles.py`
  dedupes by `ts` and stops if a page makes no progress.
- **Granularity gotcha**: strings are `15min`, `30min`, `1h` (not `30m` —
  that returns `400171`). `30min` returned `48001 Parameter validation
  failed` for June 2026 `endTime`s, while `15min` and `1h` worked for the
  whole window. 15min is used because it lands exactly on the 13:30 UTC
  cash open; `1h` stops at 13:00 and never reaches "cash open".
- **Latency / failures**: calls took several seconds each from this network,
  and one symbol-list download timed out mid-body on a 30s limit. The
  fetcher uses a 60s timeout and retries with exponential backoff (5
  attempts); failures after that abort loudly rather than writing a
  partial file silently.
- **Liquidity note**: recent bars show very small base volumes on some
  pairs (fractions of a share per bar). A traded price is real, but a
  thin bar may not absorb the configured parent size — see
  `docs/LIMITATIONS.md`.
- **Offline reproducibility**: the fetched bars are committed as
  `data/{symbol}_rtoken_15m_raw.json`; CI and fresh clones rebuild the
  dataset from them with no network access.

Live order placement is still out of scope — this is read-only market data.

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
