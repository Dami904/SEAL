import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_real_dataset.py"
spec = importlib.util.spec_from_file_location("build_real_dataset", SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def _ms(iso):
    from datetime import datetime
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


@pytest.fixture
def fake_root(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    # Fri Jun 5 and Mon Jun 8 2026 (EDT: close 20:00Z, open 13:30Z).
    daily = {"rows": [
        {"date": "2026-06-05", "open": 99.0, "close": 100.0},
        {"date": "2026-06-08", "open": 102.0, "close": 103.0},
    ]}
    (data / "tsla_ohlcv_raw.json").write_text(json.dumps(daily))
    bars = [  # bar OPEN times; each observed 15 min later
        ("2026-06-05T19:45:00Z", 100.0),  # closes 20:00 = cash close -> excluded
        ("2026-06-05T20:00:00Z", 100.5),  # first after-hours obs at 20:15
        ("2026-06-06T15:00:00Z", 101.0),  # Saturday — rToken still trades
        ("2026-06-08T13:15:00Z", 101.8),  # closes 13:30 = cash open -> last row
        ("2026-06-08T13:30:00Z", 102.1),  # cash session -> excluded
    ]
    rows = [{"ts": _ms(t), "open": p, "high": p, "low": p, "close": p,
             "base_volume": 1.0, "quote_volume": p} for t, p in bars]
    (data / "rtsla_rtoken_15m_raw.json").write_text(json.dumps({"rows": rows}))
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    return tmp_path


def test_rows_cover_only_the_cash_closed_window(fake_root):
    rows, stats = builder.build("rtsla")
    assert [r["timestamp"] for r in rows] == [
        "2026-06-05T20:15:00Z", "2026-06-06T15:15:00Z", "2026-06-08T13:30:00Z",
    ]
    assert rows[-1]["minutes_to_cash_open"] == 0
    assert rows[0]["minutes_to_cash_open"] == (2 * 24 * 60) + 17 * 60 + 15
    assert stats["nights_missing_open_bar"] == 0
    # Alignment check picks up the rToken print at the 16:00 ET close.
    assert stats["median_close_gap_pct"] == pytest.approx(0.0)


def test_rows_anchor_to_real_close_and_carry_next_open(fake_root):
    rows, _ = builder.build("rtsla")
    assert {r["date"] for r in rows} == {"2026-06-05"}
    assert all(r["cash_close"] == 100.0 and r["next_cash_open"] == 102.0 for r in rows)
    # Price is the bar's close, observed at bar close — never a future print.
    assert [r["rtoken_price"] for r in rows] == [100.5, 101.0, 101.8]
