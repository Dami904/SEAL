# Publishing to Bitget Playbook

The handbook calls Bitget Playbook "Essential" for Alpha Factory and says
entries "can submit backtest results alone" from its sandbox. Playbook's
own output (return, max drawdown, win rate, trade count, Sharpe) is missing
Sortino/turnover/IS-OOS split that judging scores, so this repo's own
`seal/backtest.py` stays the primary source of record — Playbook is a
parallel, platform-sanctioned publication path, not a dependency.

These steps require your own Bitget account login and Playbook API key —
they're not something an agent session should do on your behalf (per
CLAUDE.md: no live API keys handled by an agent).

## Steps

1. Install the GetAgent Skill:
   ```bash
   npx @bitget-ai/getagent-skill@latest install --client agent
   ```
2. Log into the Playbook platform (`https://www.bitget.com/zh-CN/activity/ai-get-agent/playbook`)
   and create a Playbook API Key (distinct from any exchange trading key).
3. Bind that key in GetAgent Studio.
4. Feed it the strategy brief below (or point it at this repo) and let it
   author/backtest/publish the strategy in its sandbox.
5. Enable Paper Trading in GetAgent Studio if you want an ongoing paper log
   alongside the backtest.

## Strategy brief (natural-language, for the agent to translate)

> Symbol: rTSLA. While NYSE/Nasdaq is closed (after-hours, weekend,
> holiday), compare the Bitget rToken price to the last official cash
> close: `spread = rtoken_price / cash_close - 1`. If `|spread|` clears
> 1.5%: on a scheduled macro event day (FOMC, CPI, named earnings), trade
> **with** the move (buy if rToken is above cash close, sell if below). On
> a non-event day, **fade** the move (bet on reversion toward cash close).
> Exit at the next cash open, on mean-reversion below half the entry
> threshold, or on a 2% adverse move against the entry spread. Cap parent
> notional at $5,000. Split the parent order into 8 clips (8–20% of
> notional each) with 5–45 second random delays between them; stop sending
> further clips if the spread reverts, the stop is hit, or cash is about to
> reopen. Assume a 6bps taker fee (paid on entry and exit) plus slippage
> that decays with more clips (impact reduction from splitting size across
> time).

This mirrors `configs/default.yaml` and `seal/signal.py` /
`seal/execution.py` / `seal/backtest.py` exactly — the brief is a
translation of the code, not a separate spec.
