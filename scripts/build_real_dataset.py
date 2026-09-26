"""Builds data/{symbol}_series.csv entirely from real market data — nothing
in the backtest input is modeled or simulated:

- rtoken_price: the actual traded Bitget rToken price (e.g. RTSLAUSDT), the
  close of each real 15-minute spot candle, from
  data/{symbol}_rtoken_15m_raw.json (fetched by fetch_rtoken_candles.py from
  Bitget's public market-data API).
- cash_close / next_cash_open: the real official close of the underlying
  stock on trading day t and the real open on trading day t+1, from
  data/{ticker}_ohlcv_raw.json (bitget-mcp-server equity_price_historical).
- event_dates: real earnings report dates (bitget-mcp-server
  equity_calendar_earnings) plus real FOMC/CPI dates.

One row per real rToken bar observed while US cash is shut: strictly after
the 16:00 ET close of day t, up to and including the 09:30 ET open of the
next trading day (weekends and holidays included — the rToken keeps
trading). A bar's price is only known at its CLOSE time (bar open + 15min),
so that is the row timestamp — no row can see a price from its own future.

next_cash_open is carried on each row only so the pre-open forecast can be
GRADED after the fact; the signal never reads it (see seal/backtest.py).
"""

import argparse
import csv
import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
NY = ZoneInfo("America/New_York")
BAR = timedelta(minutes=15)

# FOMC + August CPI — macro-wide, apply to every symbol.
MACRO_EVENT_DATES = {"2026-07-28", "2026-07-29", "2026-09-11", "2026-09-15", "2026-09-16"}

# Per-symbol earnings dates, from bitget-mcp-server's equity_calendar_earnings
# (real, verified report dates for this window).
SYMBOLS = {
    "rtsla": {"raw": "tsla_ohlcv_raw.json", "earnings": {"2026-07-22"}},
    "rnvda": {"raw": "nvda_ohlcv_raw.json", "earnings": {"2026-08-26"}},
    "raapl": {"raw": "aapl_ohlcv_raw.json", "earnings": {"2026-07-30"}},
    "ramzn": {"raw": "amzn_ohlcv_raw.json", "earnings": {"2026-07-30"}},
    "rmsft": {"raw": "msft_ohlcv_raw.json", "earnings": {"2026-07-29"}},
}

FIELDS = [
    "timestamp", "date", "rtoken_price", "cash_close",
    "minutes_to_cash_open", "next_cash_open", "rtoken_volume",
]


def event_dates_for(symbol: str) -> set[str]:
    return MACRO_EVENT_DATES | SYMBOLS[symbol]["earnings"]


def _ny(date: str, hh: int, mm: int) -> datetime:
    d = datetime.strptime(date, "%Y-%m-%d")
    return d.replace(hour=hh, minute=mm, tzinfo=NY).astimezone(timezone.utc)


def load_rtoken_bars(symbol: str) -> list[tuple[datetime, float, float]]:
    """(observation time = bar close, close price, base volume), sorted."""
    raw = json.loads((ROOT / "data" / f"{symbol}_rtoken_15m_raw.json").read_text())["rows"]
    bars = [
        (datetime.fromtimestamp(r["ts"] / 1000, tz=timezone.utc) + BAR, r["close"], r["base_volume"])
        for r in raw
    ]
    return sorted(bars)


def build(symbol: str) -> tuple[list[dict], dict]:
    daily = json.loads((ROOT / "data" / SYMBOLS[symbol]["raw"]).read_text())["rows"]
    bars = load_rtoken_bars(symbol)

    out: list[dict] = []
    nights_missing_open = 0
    close_gaps = []
    for day, next_day in zip(daily, daily[1:]):
        close_t = _ny(day["date"], 16, 0)
        open_t = _ny(next_day["date"], 9, 30)
        night = [b for b in bars if close_t < b[0] <= open_t]
        if not night:
            continue
        if night[-1][0] != open_t:
            nights_missing_open += 1

        # Alignment sanity check: the rToken print at the cash close should
        # sit close to the official close if timestamps/timezones are right.
        at_close = [b for b in bars if b[0] == close_t]
        if at_close:
            close_gaps.append(abs(at_close[0][1] / day["close"] - 1))

        for obs_t, price, volume in night:
            out.append({
                "timestamp": obs_t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "date": day["date"],
                "rtoken_price": price,
                "cash_close": day["close"],
                "minutes_to_cash_open": int((open_t - obs_t).total_seconds() // 60),
                "next_cash_open": next_day["open"],
                "rtoken_volume": volume,
            })

    stats = {
        "rows": len(out),
        "nights": len({r["date"] for r in out}),
        "nights_missing_open_bar": nights_missing_open,
        "zero_volume_rows": sum(1 for r in out if r["rtoken_volume"] == 0),
        "median_close_gap_pct": 100 * statistics.median(close_gaps) if close_gaps else None,
    }
    return out, stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="rtsla", choices=sorted(SYMBOLS.keys()),
                        help="which symbol to build (default: rtsla)")
    parser.add_argument("--all", action="store_true", help="build every symbol")
    args = parser.parse_args()

    for symbol in list(SYMBOLS.keys()) if args.all else [args.symbol]:
        rows, stats = build(symbol)
        out_path = ROOT / "data" / f"{symbol}_series.csv"
        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{symbol}: {stats} -> {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
