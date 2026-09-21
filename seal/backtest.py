"""Parent-level backtest: one trade at a time, entered on an after-hours
spread signal and exited on mean-reversion, stop, or cash reopen.

Scored on the PARENT (one fill at the average clip price), not per-child —
see README "Execution (Seal)".
"""

import math
import random
from dataclasses import dataclass, field, replace

import pandas as pd

from seal.params import Params
from seal.execution import clip_sizes, should_cancel_remaining
from seal.signal import compute_spread, is_event_window, parent_side

SIDE_SIGN = {"long": 1.0, "short": -1.0}


def _cost_bps(params: Params, clip_count: int) -> float:
    """Taker fee (paid twice, entry+exit) plus market-impact slippage that
    DECAYS as clip_count grows — splitting size across time-jittered clips
    is what reduces impact vs. a one-shot print, so more clips must cost
    less, not more. Square-root decay is the standard simplification for
    impact reduction from time-diversified execution."""
    return 2 * params.taker_fee_bps + params.slippage_bps_per_clip / math.sqrt(clip_count)


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: str
    entry_price: float
    exit_price: float
    notional: float
    clip_count: int
    net_pnl_pct: float
    pnl_dollars: float
    anchor_cash_close: float
    forecast_price: float
    next_cash_open: float | None = None


TRADING_DAYS_PER_YEAR = 252


def _daily_returns(trades: list[Trade]) -> pd.Series:
    """Trade net_pnl_pct resampled to a calendar-daily series (0 on days
    with no exit), so Sharpe/Sortino are computed on the same basis a
    standard annualized daily return series would use — not scaled by raw
    trade count, which inflates with trade frequency regardless of elapsed
    time."""
    if not trades:
        return pd.Series(dtype=float)
    daily: dict = {}
    for t in trades:
        day = t.exit_time.normalize()
        daily[day] = daily.get(day, 0.0) + t.net_pnl_pct
    series = pd.Series(daily).sort_index()
    full_range = pd.date_range(series.index.min(), series.index.max(), freq="D")
    return series.reindex(full_range, fill_value=0.0)


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)

    def metrics(self) -> dict:
        if not self.trades:
            return {
                "trade_count": 0, "total_pnl": 0.0, "sharpe": 0.0,
                "sortino": 0.0, "max_drawdown": 0.0, "turnover": 0.0,
                "forecast": {"count": 0, "mae_pct": 0.0, "directional_count": 0, "directional_accuracy": None},
            }
        total_pnl = sum(t.pnl_dollars for t in self.trades)
        turnover = sum(t.notional * 2 for t in self.trades)

        daily = _daily_returns(self.trades)
        mean, std = daily.mean(), daily.std(ddof=1) if len(daily) > 1 else 0.0
        sharpe = (mean / std) * math.sqrt(TRADING_DAYS_PER_YEAR) if std > 0 else 0.0

        downside = daily[daily < 0]
        down_std = downside.std(ddof=1) if len(downside) > 1 else 0.0
        sortino = (mean / down_std) * math.sqrt(TRADING_DAYS_PER_YEAR) if down_std > 0 else 0.0

        equity = self.equity_curve["equity"] if not self.equity_curve.empty else pd.Series([0.0])
        running_max = equity.cummax()
        drawdown = (equity - running_max)
        max_drawdown = drawdown.min() if len(drawdown) else 0.0

        return {
            "trade_count": len(self.trades),
            "total_pnl": float(total_pnl),
            "sharpe": float(sharpe),
            "sortino": float(sortino),
            "max_drawdown": float(max_drawdown),
            "turnover": float(turnover),
            "forecast": self.forecast_accuracy(),
        }

    def forecast_accuracy(self) -> dict:
        """MAE is scored over every trade with a known realized open. Directional
        accuracy is scored only over trades with a non-flat forecast (the
        "follow" side) — a "fade" forecast is intentionally flat vs. the
        anchor close, so it makes no directional call to grade; penalizing
        it as an automatic miss would just be counting fade trades twice."""
        scored = [t for t in self.trades if t.next_cash_open is not None]
        if not scored:
            return {"count": 0, "mae_pct": 0.0, "directional_count": 0, "directional_accuracy": None}

        errors = [abs(t.forecast_price - t.next_cash_open) / t.next_cash_open for t in scored]

        directional = [t for t in scored if t.forecast_price != t.anchor_cash_close]
        hits = sum(
            1 for t in directional
            if (t.forecast_price > t.anchor_cash_close) == (t.next_cash_open > t.anchor_cash_close)
        )

        return {
            "count": len(scored),
            "mae_pct": float(sum(errors) / len(errors)),
            "directional_count": len(directional),
            "directional_accuracy": float(hits / len(directional)) if directional else None,
        }


def run_backtest(df: pd.DataFrame, params: Params, seed: int = 0) -> BacktestResult:
    rng = random.Random(seed)
    trades: list[Trade] = []
    equity = 0.0
    equity_rows = []

    position = None  # dict while a trade is open

    for _, row in df.iterrows():
        if position is None:
            spread = compute_spread(row["rtoken_price"], row["cash_close"])
            event = is_event_window(row["date"], params.event_dates)
            side = parent_side(spread, params.entry_threshold, event)
            if side is not None:
                clips = clip_sizes(
                    params.tier_notional, params.clip_count,
                    params.clip_min_pct, params.clip_max_pct, rng,
                )
                # Trust the print when the move is event-corroborated ("follow");
                # trust the prior close when it's not ("fade") — same logic that
                # picks the trade side, exposed as a price forecast (the reframe).
                forecast_price = row["rtoken_price"] if event else row["cash_close"]
                position = {
                    "entry_time": row["timestamp"],
                    "side": side,
                    "entry_price": row["rtoken_price"],
                    "anchor_cash_close": row["cash_close"],
                    "notional": sum(clips),
                    "clip_count": len(clips),
                    "forecast_price": forecast_price,
                    "next_cash_open": row.get("next_cash_open"),
                }
            continue

        sign = SIDE_SIGN[position["side"]]
        current_spread = compute_spread(row["rtoken_price"], position["anchor_cash_close"])
        entry_spread = compute_spread(position["entry_price"], position["anchor_cash_close"])
        adverse_move = sign * (current_spread - entry_spread)
        stop_hit = adverse_move <= -params.stop_loss

        if should_cancel_remaining(current_spread, params.entry_threshold, stop_hit,
                                    row["minutes_to_cash_open"]):
            exit_price = row["rtoken_price"]
            raw_pnl_pct = sign * (exit_price - position["entry_price"]) / position["entry_price"]
            cost_bps = _cost_bps(params, position["clip_count"])
            net_pnl_pct = raw_pnl_pct - cost_bps / 10_000
            pnl_dollars = position["notional"] * net_pnl_pct
            equity += pnl_dollars
            trades.append(Trade(
                entry_time=position["entry_time"], exit_time=row["timestamp"],
                side=position["side"], entry_price=position["entry_price"],
                exit_price=exit_price, notional=position["notional"],
                clip_count=position["clip_count"], net_pnl_pct=net_pnl_pct,
                pnl_dollars=pnl_dollars, anchor_cash_close=position["anchor_cash_close"],
                forecast_price=position["forecast_price"],
                next_cash_open=position["next_cash_open"],
            ))
            equity_rows.append({"timestamp": row["timestamp"], "equity": equity})
            position = None

    equity_curve = pd.DataFrame(equity_rows) if equity_rows else pd.DataFrame(columns=["timestamp", "equity"])
    return BacktestResult(trades=trades, equity_curve=equity_curve)


def split_metrics(df: pd.DataFrame, params: Params, split_date: str, seed: int = 0) -> dict:
    """In-sample / out-of-sample split. `split_date` rows go to OOS (>=),
    everything before goes to IS. Reports the handbook's own decay
    reference: oos_sharpe / is_sharpe, flagged if < 0.5."""
    is_df = df[df["date"] < split_date]
    oos_df = df[df["date"] >= split_date]

    is_result = run_backtest(is_df, params, seed=seed)
    oos_result = run_backtest(oos_df, params, seed=seed)
    is_metrics = is_result.metrics()
    oos_metrics = oos_result.metrics()

    is_sharpe = is_metrics["sharpe"]
    decay_ratio = (oos_metrics["sharpe"] / is_sharpe) if is_sharpe != 0 else None

    return {
        "split_date": split_date,
        "in_sample": is_metrics,
        "out_of_sample": oos_metrics,
        "oos_decay_ratio": float(decay_ratio) if decay_ratio is not None else None,
        "oos_decay_flag": bool(decay_ratio is not None and decay_ratio < 0.5),
    }


def rolling_sharpe(result: BacktestResult, window_days: int = 30) -> list[dict]:
    """Rolling `window_days`-wide Sharpe over the daily P&L series, annualized
    on the same sqrt(252) basis as the headline Sharpe (handbook: "rolling
    30-day Sharpe stability") — a window is for stability/decay, not a
    change in annualization convention."""
    if not result.trades:
        return []

    daily = _daily_returns(result.trades)
    min_periods = max(5, window_days // 3)
    roll_mean = daily.rolling(window_days, min_periods=min_periods).mean()
    roll_std = daily.rolling(window_days, min_periods=min_periods).std(ddof=1)
    roll_sharpe = (roll_mean / roll_std) * math.sqrt(TRADING_DAYS_PER_YEAR)

    out = []
    for date, value in roll_sharpe.items():
        if pd.notna(value):
            out.append({"date": date.strftime("%Y-%m-%d"), "sharpe": float(value)})
    return out


def cost_gap(df: pd.DataFrame, params: Params, seed: int = 0) -> dict:
    """One-shot (clip_count=1, full notional in one print) vs. the
    configured multi-clip execution — proves the Seal execution layer earns
    its place, per README: "Seal is doing its job if clipped results stay
    inside your impact budget." """
    one_shot_params = replace(params, clip_count=1, clip_min_pct=1.0, clip_max_pct=1.0)

    clipped = run_backtest(df, params, seed=seed).metrics()
    one_shot = run_backtest(df, one_shot_params, seed=seed).metrics()

    return {
        "clipped": {"total_pnl": clipped["total_pnl"], "sharpe": clipped["sharpe"]},
        "one_shot": {"total_pnl": one_shot["total_pnl"], "sharpe": one_shot["sharpe"]},
        "pnl_improvement": clipped["total_pnl"] - one_shot["total_pnl"],
    }
