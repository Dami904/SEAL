"""SEAL signal: rToken vs last cash close, with event-aware side selection."""

from typing import Optional


def compute_spread(rtoken_price: float, cash_close: float) -> float:
    if cash_close <= 0:
        raise ValueError("cash_close must be positive")
    return rtoken_price / cash_close - 1.0


def is_event_window(date: str, event_dates: frozenset[str]) -> bool:
    return date in event_dates


def parent_side(spread: float, threshold: float, is_event: bool) -> Optional[str]:
    """Return "long", "short", or None if the spread doesn't clear the threshold.

    Event window: trade with the move (spread direction = side direction).
    No event: fade the spike (empty-book overreaction assumed to mean-revert).
    """
    if abs(spread) < threshold:
        return None
    moved_up = spread > 0
    trade_with_move = moved_up if is_event else not moved_up
    return "long" if trade_with_move else "short"
