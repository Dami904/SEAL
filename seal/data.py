"""Loads the prepared after-hours price series used by the backtest.

Input CSV contract (one row per after-hours rToken observation you want to
evaluate as a possible entry), columns:

    timestamp            ISO 8601, UTC (e.g. 2026-01-05T22:15:00Z)
    date                 US trading-day this observation anchors to (YYYY-MM-DD)
    rtoken_price          last Bitget rToken price at `timestamp`
    cash_close            official close of the underlying stock for `date`
    minutes_to_cash_open  minutes until the next NYSE/Nasdaq regular-hours open

Building the cash-close/calendar alignment itself (timezones, half-days,
holidays) is out of scope here — see docs/LIMITATIONS.md. This module only
validates and loads an already-aligned series.
"""

import pandas as pd

REQUIRED_COLUMNS = [
    "timestamp",
    "date",
    "rtoken_price",
    "cash_close",
    "minutes_to_cash_open",
]


def load_series(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    if (df["cash_close"] <= 0).any():
        raise ValueError(f"{path} has non-positive cash_close values")
    if (df["rtoken_price"] <= 0).any():
        raise ValueError(f"{path} has non-positive rtoken_price values")
    return df
