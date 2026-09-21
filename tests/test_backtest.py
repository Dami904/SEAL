import pandas as pd
import pytest

from seal.backtest import cost_gap, rolling_sharpe, run_backtest, split_metrics
from seal.params import Params


def make_params(**overrides):
    base = dict(
        symbol="TEST", entry_threshold=0.015, stop_loss=0.02, tier_notional=1000,
        clip_count=4, clip_min_pct=0.1, clip_max_pct=0.4,
        jitter_min_seconds=1, jitter_max_seconds=5,
        taker_fee_bps=5, slippage_bps_per_clip=2, event_dates=frozenset(),
    )
    base.update(overrides)
    return Params(**base)


def ts(hour):
    return pd.Timestamp(f"2026-01-05T{hour:02d}:00:00Z")


def test_no_trade_when_spread_never_triggers():
    df = pd.DataFrame([
        {"timestamp": ts(18), "date": "2026-01-05", "rtoken_price": 100.5,
         "cash_close": 100.0, "minutes_to_cash_open": 600},
        {"timestamp": ts(20), "date": "2026-01-05", "rtoken_price": 100.8,
         "cash_close": 100.0, "minutes_to_cash_open": 480},
    ])
    result = run_backtest(df, make_params())
    assert result.trades == []


def test_long_trade_opens_and_closes_at_cash_reopen():
    df = pd.DataFrame([
        # entry: rToken 3% above cash close, no event -> fade -> short... use down move instead
        {"timestamp": ts(18), "date": "2026-01-05", "rtoken_price": 97.0,
         "cash_close": 100.0, "minutes_to_cash_open": 600},   # spread -3% -> fade -> long
        {"timestamp": ts(20), "date": "2026-01-05", "rtoken_price": 98.0,
         "cash_close": 100.0, "minutes_to_cash_open": 60},
        {"timestamp": ts(22), "date": "2026-01-05", "rtoken_price": 99.0,
         "cash_close": 100.0, "minutes_to_cash_open": 0},     # cash about to open -> forced exit
    ])
    result = run_backtest(df, make_params())
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.side == "long"
    assert trade.entry_price == 97.0
    assert trade.exit_price == 99.0
    assert trade.net_pnl_pct > 0  # price rose while long, net of costs
    metrics = result.metrics()
    assert metrics["trade_count"] == 1
    assert metrics["total_pnl"] == pytest.approx(trade.pnl_dollars)


def test_costs_reduce_pnl_versus_raw_move():
    df = pd.DataFrame([
        {"timestamp": ts(18), "date": "2026-01-05", "rtoken_price": 97.0,
         "cash_close": 100.0, "minutes_to_cash_open": 600},
        {"timestamp": ts(22), "date": "2026-01-05", "rtoken_price": 97.0,
         "cash_close": 100.0, "minutes_to_cash_open": 0},  # flat move, forced exit
    ])
    result = run_backtest(df, make_params())
    trade = result.trades[0]
    raw_pnl_pct = 0.0  # price didn't move
    assert trade.net_pnl_pct < raw_pnl_pct  # fees + slippage make flat trades a loser


def _day(date, up=False):
    """One fade-trade night: -3% spread, no event, forced exit at reopen."""
    entry, mid, exit_ = (103.0, 102.0, 101.0) if up else (97.0, 98.0, 99.0)
    return [
        {"timestamp": pd.Timestamp(f"{date}T18:00:00Z"), "date": date,
         "rtoken_price": entry, "cash_close": 100.0, "minutes_to_cash_open": 600,
         "next_cash_open": 99.5},
        {"timestamp": pd.Timestamp(f"{date}T20:00:00Z"), "date": date,
         "rtoken_price": mid, "cash_close": 100.0, "minutes_to_cash_open": 60,
         "next_cash_open": 99.5},
        {"timestamp": pd.Timestamp(f"{date}T22:00:00Z"), "date": date,
         "rtoken_price": exit_, "cash_close": 100.0, "minutes_to_cash_open": 0,
         "next_cash_open": 99.5},
    ]


def test_split_metrics_separates_is_and_oos():
    rows = _day("2026-01-05") + _day("2026-01-06") + _day("2026-02-10") + _day("2026-02-11")
    df = pd.DataFrame(rows)
    result = split_metrics(df, make_params(), split_date="2026-02-01")
    assert result["in_sample"]["trade_count"] == 2
    assert result["out_of_sample"]["trade_count"] == 2
    assert result["split_date"] == "2026-02-01"
    assert "oos_decay_ratio" in result


def test_rolling_sharpe_returns_series_once_enough_days():
    rows = []
    for i in range(10):
        rows += _day(f"2026-01-{5 + i:02d}")
    df = pd.DataFrame(rows)
    result = run_backtest(df, make_params())
    series = rolling_sharpe(result, window_days=5)
    assert len(series) > 0
    assert all("date" in p and "sharpe" in p for p in series)


def test_cost_gap_clipping_beats_one_shot():
    rows = _day("2026-01-05")
    df = pd.DataFrame(rows)
    result = cost_gap(df, make_params(clip_count=8))
    # sqrt-decay cost model: more clips -> lower slippage bps -> better PnL
    # than a one-shot (clip_count=1) print of the same signal.
    assert result["clipped"]["total_pnl"] > result["one_shot"]["total_pnl"]


def test_forecast_accuracy_scores_fade_trade_against_realized_open():
    rows = _day("2026-01-05")  # fade trade: forecast_price = anchor_cash_close = 100.0
    df = pd.DataFrame(rows)
    result = run_backtest(df, make_params())
    forecast = result.forecast_accuracy()
    assert forecast["count"] == 1
    # forecast (100.0) vs realized next_cash_open (99.5)
    assert forecast["mae_pct"] == pytest.approx(0.5 / 99.5)
    # forecast direction (100 vs anchor 100 = flat) -> a fade makes no
    # directional call, so it's excluded from directional scoring entirely
    assert forecast["directional_count"] == 0
    assert forecast["directional_accuracy"] is None


def test_forecast_accuracy_scores_follow_trade_directionally():
    df = pd.DataFrame([
        {"timestamp": ts(18), "date": "2026-01-05", "rtoken_price": 104.0,
         "cash_close": 100.0, "minutes_to_cash_open": 600, "next_cash_open": 105.0},
        {"timestamp": ts(22), "date": "2026-01-05", "rtoken_price": 106.0,
         "cash_close": 100.0, "minutes_to_cash_open": 0, "next_cash_open": 105.0},
    ])
    result = run_backtest(df, make_params(event_dates=frozenset({"2026-01-05"})))
    forecast = result.trades[0]
    assert forecast.forecast_price == 104.0  # event -> trust the print, not the anchor
    accuracy = result.forecast_accuracy()
    assert accuracy["directional_count"] == 1
    assert accuracy["directional_accuracy"] == 1.0  # forecast up, realized up -> hit
