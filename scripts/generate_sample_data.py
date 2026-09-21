"""Generates a SYNTHETIC after-hours price series — a standalone convenience
for exploring `run_backtest.py` without pulling real data first.

Not used by pytest or CI (the test suite builds its own tiny in-memory
DataFrames; CI rebuilds the real dataset from the committed
data/tsla_ohlcv_raw.json via build_real_dataset.py). This is not real
market data — point `configs/default.yaml`'s `data_path` at
data/real_series.csv (the default) before publishing backtest results.
"""

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_series.csv"
DAYS = 75
ROWS_PER_DAY = 6


def generate(seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    cash_close = 250.0
    start = datetime(2026, 1, 5, tzinfo=timezone.utc)

    for day in range(DAYS):
        date = start + timedelta(days=day)
        if date.weekday() >= 5:
            continue  # cash market only closes weekdays too; rToken still trades weekends
        cash_close *= 1 + rng.uniform(-0.01, 0.01)
        rtoken_price = cash_close
        for r in range(ROWS_PER_DAY):
            shock = rng.uniform(-0.03, 0.03) if rng.random() < 0.2 else rng.uniform(-0.008, 0.008)
            rtoken_price *= 1 + shock
            ts = date + timedelta(hours=18 + r * 2)
            minutes_to_open = max(0, (16 - r) * 60 - r * 15)
            rows.append({
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "date": date.strftime("%Y-%m-%d"),
                "rtoken_price": round(rtoken_price, 4),
                "cash_close": round(cash_close, 4),
                "minutes_to_cash_open": minutes_to_open,
            })
    return rows


def main() -> None:
    rows = generate()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "date", "rtoken_price", "cash_close", "minutes_to_cash_open",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
