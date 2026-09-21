"""Seal: split a parent order into clips and decide when to stop clipping."""

import random


def clip_sizes(total_notional: float, clip_count: int, clip_min_pct: float,
                clip_max_pct: float, rng: random.Random) -> list[float]:
    """Split total_notional into clip_count clips, each within [min_pct, max_pct]
    of the total, normalized to sum exactly to total_notional."""
    if clip_count < 1:
        raise ValueError("clip_count must be >= 1")
    if clip_min_pct > clip_max_pct:
        raise ValueError("clip_min_pct must be <= clip_max_pct")
    raw = [rng.uniform(clip_min_pct, clip_max_pct) for _ in range(clip_count)]
    total_pct = sum(raw)
    return [total_notional * (pct / total_pct) for pct in raw]


def jitter_delay(min_seconds: float, max_seconds: float, rng: random.Random) -> float:
    if min_seconds > max_seconds:
        raise ValueError("min_seconds must be <= max_seconds")
    return rng.uniform(min_seconds, max_seconds)


def should_cancel_remaining(current_spread: float, entry_threshold: float,
                             stop_hit: bool, minutes_to_cash_open: float) -> bool:
    """Stop sending further clips once the edge that justified the parent
    order is gone, the stop is hit, or cash is about to reopen."""
    if stop_hit:
        return True
    if minutes_to_cash_open <= 0:
        return True
    if abs(current_spread) < entry_threshold * 0.5:
        return True
    return False
