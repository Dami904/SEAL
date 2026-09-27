# Publishing to Bitget Playbook

**Status: not published.** A Playbook package for rTSLA was authored with
the GetAgent Skill and passed its local validator, but it was not uploaded
for this submission (see "What blocked it" below). The handbook lists
Playbook as optional but recommended for Alpha Factory. This repo's own
`seal/backtest.py` is the source of record either way: Playbook's displayed
output (return, max drawdown, win rate, trade count, Sharpe) does not
include the Sortino, turnover or IS/OOS split that judging scores.

## Steps (for publishing later)

1. Install the GetAgent Skill for your agent client:
   ```bash
   npx @bitget-ai/getagent-skill@latest install --client claude
   ```
   Valid clients are `claude`, `cursor`, `codex` and `all`.
2. Log into the Playbook platform
   (`https://www.bitget.com/activity/ai-get-agent/playbook`) and create a
   **Playbook key**. An exchange API key from Bitget's API Management page
   does not work: the upload endpoint rejects it with
   `4100 No user found for the provided playbook_key`.
3. Bind that key in GetAgent Studio.
4. Author the package from the strategy brief below, validate it locally
   with the skill's `scripts/validate.py`, then upload and run a sandbox
   backtest.
5. Optionally enable Paper Trading in GetAgent Studio for an ongoing
   paper log alongside the backtest.

## What blocked it

- **Key type.** The skill's docs describe the credential as a "Bitget
  OpenAPI ACCESS-KEY"; the endpoint actually requires a Playbook key.
  There was not enough time before the deadline to obtain one.
- **Network.** On our network, DNS for Bitget hosts failed intermittently
  and `agent.bitget.com` was unreachable (see `docs/API_NOTES.md`).

## Design notes from the drafted package

- **Data:** real `RTSLAUSDT` 15-minute spot bars (`exchange="bitget"`),
  anchored to the token's own print at the 16:00 ET close, which sits
  within about 0.02% of the official close.
- **Fees:** Bitget's published rToken spot fee, 0.10% per side.
- **Shorting:** rToken spot cannot be shorted, so a live follow-trade
  Playbook can only execute the long side. A faithful replay of SEAL needs
  a margin venue in the backtest spec, and the live and backtest results
  would differ; this must be stated in the Playbook's description.

## Strategy brief (natural language, for the agent to translate)

> Symbol: rTSLA (`RTSLAUSDT` spot). While NYSE/Nasdaq is closed
> (after-hours, weekend, holiday), compare the Bitget rToken price to the
> last official cash close: `spread = rtoken_price / cash_close - 1`. If
> `|spread|` clears 1.5%: on a scheduled event night (FOMC, CPI, the
> company's earnings), trade **with** the move (buy if the rToken is above
> the cash close, sell if below). On a quiet night, **fade** the move (bet
> on reversion toward the cash close). Exit at the next cash open, on
> mean-reversion below half the entry threshold, or on a 2% adverse move
> against the entry spread. Cap parent notional at $5,000. Split the
> parent order into 8 clips (8–20% of notional each) with 5–45 second
> random delays between them; stop sending clips if the spread reverts,
> the stop is hit, or cash is about to reopen. Charge Bitget's 0.10% spot
> fee on entry and exit, plus slippage that decays with more clips.

This mirrors `configs/default.yaml` and `seal/signal.py` /
`seal/execution.py` / `seal/backtest.py`: the brief is a translation of
the code, not a separate spec.
