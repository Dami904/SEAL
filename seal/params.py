from dataclasses import dataclass


@dataclass(frozen=True)
class Params:
    symbol: str
    entry_threshold: float
    stop_loss: float
    tier_notional: float
    clip_count: int
    clip_min_pct: float
    clip_max_pct: float
    jitter_min_seconds: float
    jitter_max_seconds: float
    taker_fee_bps: float
    slippage_bps_per_clip: float
    event_dates: frozenset[str]

    @staticmethod
    def from_dict(d: dict) -> "Params":
        return Params(
            symbol=d["symbol"],
            entry_threshold=float(d["entry_threshold"]),
            stop_loss=float(d["stop_loss"]),
            tier_notional=float(d["tier_notional"]),
            clip_count=int(d["clip_count"]),
            clip_min_pct=float(d["clip_min_pct"]),
            clip_max_pct=float(d["clip_max_pct"]),
            jitter_min_seconds=float(d["jitter_min_seconds"]),
            jitter_max_seconds=float(d["jitter_max_seconds"]),
            taker_fee_bps=float(d["taker_fee_bps"]),
            slippage_bps_per_clip=float(d["slippage_bps_per_clip"]),
            event_dates=frozenset(d.get("event_dates", [])),
        )
