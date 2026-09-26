"""Fetches REAL Bitget rToken spot candles (e.g. RTSLAUSDT) from Bitget's
public market-data API and writes them to data/{slug}_rtoken_15m_raw.json.

This replaces the old modeled after-hours path: every rtoken_price the
backtest sees is now an actual traded Bitget rToken price.

Endpoint: GET https://api.bitget.com/api/v2/spot/market/history-candles
(public, no API key). Max 200 candles per call, paginated backward via
endTime. 15-minute bars are used because they land exactly on the 13:30 UTC
(09:30 ET) cash open, so the last observation of each night is the open
itself — hourly bars would stop at 13:00 and never reach "cash open".

Run once (needs network); the output is committed so CI and anyone cloning
the repo rebuild the dataset offline.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://api.bitget.com/api/v2/spot/market/history-candles"
GRANULARITY = "15min"
BAR_MS = 15 * 60 * 1000
PAGE_LIMIT = 200
MAX_RETRIES = 5

SYMBOLS = {
    "rtsla": "RTSLAUSDT",
    "rnvda": "RNVDAUSDT",
    "raapl": "RAAPLUSDT",
    "ramzn": "RAMZNUSDT",
    "rmsft": "RMSFTUSDT",
}


def _ms(date: str) -> int:
    return int(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def _get(pair: str, end_ms: int) -> list[list[str]]:
    query = f"?symbol={pair}&granularity={GRANULARITY}&endTime={end_ms}&limit={PAGE_LIMIT}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(URL + query, timeout=60) as resp:
                body = json.loads(resp.read())
            if body.get("code") != "00000":
                raise RuntimeError(f"Bitget error {body.get('code')}: {body.get('msg')}")
            return body["data"] or []
        except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = 2 ** attempt
            print(f"  {pair} endTime={end_ms}: {exc!r}, retry {attempt}/{MAX_RETRIES} in {wait}s",
                  file=sys.stderr)
            time.sleep(wait)
    return []


def fetch(pair: str, start: str, end: str) -> list[dict]:
    start_ms, end_ms = _ms(start), _ms(end)
    bars: dict[int, dict] = {}
    cursor = end_ms
    while cursor > start_ms:
        page = _get(pair, cursor)
        if not page:
            break
        for ts, o, h, low, c, base_vol, quote_vol, *_ in page:
            t = int(ts)
            if start_ms <= t < end_ms:
                bars[t] = {"ts": t, "open": float(o), "high": float(h), "low": float(low),
                           "close": float(c), "base_volume": float(base_vol),
                           "quote_volume": float(quote_vol)}
        oldest = min(int(row[0]) for row in page)
        if oldest >= cursor:  # no progress — avoid an infinite loop
            break
        cursor = oldest
        time.sleep(0.1)  # stay well under Bitget's public rate limit
    return [bars[t] for t in sorted(bars)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", choices=sorted(SYMBOLS), help="one symbol (default: all)")
    parser.add_argument("--start", default="2026-06-01")
    parser.add_argument("--end", default="2026-09-22", help="exclusive, UTC")
    args = parser.parse_args()

    for slug in [args.symbol] if args.symbol else list(SYMBOLS):
        pair = SYMBOLS[slug]
        rows = fetch(pair, args.start, args.end)
        expected = (_ms(args.end) - _ms(args.start)) // BAR_MS
        out = {
            "source": f"Bitget public API {URL}",
            "pair": pair,
            "granularity": GRANULARITY,
            "bar_timestamp": "bar OPEN time, ms UTC; close is the price at ts + 15min",
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "start_date": args.start,
            "end_date_exclusive": args.end,
            "rows": rows,
        }
        path = ROOT / "data" / f"{slug}_rtoken_15m_raw.json"
        # One bar per line keeps the committed file diff-friendly.
        body = ",\n".join(json.dumps(r, separators=(",", ":")) for r in rows)
        header = json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2)[:-2]
        path.write_text(f'{header},\n  "rows": [\n{body}\n]\n}}\n')
        print(f"{pair}: {len(rows)}/{expected} bars -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
