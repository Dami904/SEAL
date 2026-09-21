"""Builds data/real_series.csv from real TSLA daily OHLCV (data/tsla_ohlcv_raw.json,
fetched via bitget-mcp-server's equity_price_historical) plus a documented,
explicitly-modeled after-hours rToken price.

What's real: cash_close[t] and next_cash_open[t] (the actual close and the
actual next trading day's open) come straight from the fetched daily bars —
this is the ground truth the strategy is scored against and what the
pre-open fair-value forecast is graded on.

What's modeled (NOT real tick data, no Bitget rToken feed exists to us yet
— see docs/LIMITATIONS.md): the after-hours rtoken_price PATH between
close[t] and open[t+1], both of which are real. The path is built so it
converges toward the real next_cash_open as the window progresses — by the
final (exit) observation the rToken price is close to the true realized
open, not another independent random draw. This matters: an earlier version
of this generator drew every observation as an independent noise sample,
which meant "fade" trades won mostly because an entry conditioned on a
large draw regressed toward a smaller independent draw by chance — a
statistical artifact, not the strategy's real thesis. The fix models two
regimes instead:

- Event nights (verified FOMC/CPI/earnings dates): the print leaks a
  meaningful fraction of the true move early and converges toward ~90% of
  it by the close of the window, with small residual noise throughout —
  real information gets priced in efficiently.
- Non-event nights: an early spurious overreaction (noise, front-loaded)
  that DECAYS as the window progresses, converging toward the small real
  close-to-open move by the final observation — the "fade" trade wins when
  the early spike genuinely doesn't persist, which is what the real
  (unmanipulated) next_cash_open determines, not a coincidence of two
  independent draws.
"""

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "tsla_ohlcv_raw.json"
OUT_PATH = ROOT / "data" / "real_series.csv"

EVENT_DATES = {
    "2026-07-22",  # Tesla Q2 2026 earnings, after close
    "2026-07-28", "2026-07-29",  # FOMC
    "2026-09-11",  # August CPI
    "2026-09-15", "2026-09-16",  # FOMC
}

ROWS_PER_NIGHT = 3
EVENT_REVEAL_START = 0.30      # fraction of true move already priced in at the first print
EVENT_REVEAL_END = 0.90        # fraction priced in by the last print before reopen
EVENT_NOISE_STD = 0.004
NON_EVENT_NOISE_STD = 0.020    # overreaction magnitude, decays to ~0 by reopen
NON_EVENT_RESIDUAL_STD = 0.003  # residual noise remaining even at the final print


def build(seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    raw = json.loads(RAW_PATH.read_text())["rows"]

    out = []
    for i in range(len(raw) - 1):
        day, next_day = raw[i], raw[i + 1]
        date = day["date"]
        cash_close = day["close"]
        next_open = next_day["open"]
        true_move = next_open / cash_close - 1.0
        is_event = date in EVENT_DATES

        base_dt = datetime.strptime(date, "%Y-%m-%d").replace(
            hour=20, minute=0, tzinfo=timezone.utc
        )
        for j in range(ROWS_PER_NIGHT):
            progress = (j + 1) / ROWS_PER_NIGHT  # 0.33, 0.67, 1.0 -> closer to open
            if is_event:
                reveal = EVENT_REVEAL_START + (EVENT_REVEAL_END - EVENT_REVEAL_START) * progress
                implied_move = true_move * reveal + rng.gauss(0, EVENT_NOISE_STD)
            else:
                # true_move is real and usually small on a non-event night; the
                # observed spread comes mostly from front-loaded overreaction
                # noise that fades out as the window progresses toward reopen.
                reveal = progress
                overreaction_std = NON_EVENT_NOISE_STD * (1 - progress) + NON_EVENT_RESIDUAL_STD
                implied_move = true_move * reveal + rng.gauss(0, overreaction_std)

            rtoken_price = cash_close * (1 + implied_move)
            ts = base_dt + timedelta(hours=j * 3)
            minutes_to_open = max(0, round((1 - progress) * 12 * 60))

            out.append({
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "date": date,
                "rtoken_price": round(rtoken_price, 4),
                "cash_close": round(cash_close, 4),
                "minutes_to_cash_open": minutes_to_open,
                "next_cash_open": round(next_open, 4),
            })
    return out


def main() -> None:
    import csv

    rows = build()
    with OUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "date", "rtoken_price", "cash_close",
            "minutes_to_cash_open", "next_cash_open",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
