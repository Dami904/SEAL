import random

import pytest

from seal.execution import clip_sizes, jitter_delay, should_cancel_remaining


def test_clip_sizes_sums_to_total():
    rng = random.Random(1)
    sizes = clip_sizes(1000, clip_count=8, clip_min_pct=0.08, clip_max_pct=0.20, rng=rng)
    assert len(sizes) == 8
    assert sum(sizes) == pytest.approx(1000)
    assert all(s > 0 for s in sizes)


def test_clip_sizes_rejects_bad_bounds():
    rng = random.Random(1)
    with pytest.raises(ValueError):
        clip_sizes(1000, clip_count=4, clip_min_pct=0.5, clip_max_pct=0.1, rng=rng)
    with pytest.raises(ValueError):
        clip_sizes(1000, clip_count=0, clip_min_pct=0.1, clip_max_pct=0.5, rng=rng)


def test_jitter_delay_within_bounds():
    rng = random.Random(2)
    for _ in range(50):
        d = jitter_delay(5, 45, rng)
        assert 5 <= d <= 45


def test_should_cancel_on_stop_hit():
    assert should_cancel_remaining(0.02, 0.015, stop_hit=True, minutes_to_cash_open=100) is True


def test_should_cancel_when_cash_about_to_open():
    assert should_cancel_remaining(0.02, 0.015, stop_hit=False, minutes_to_cash_open=0) is True


def test_should_cancel_when_edge_gone():
    assert should_cancel_remaining(0.005, 0.015, stop_hit=False, minutes_to_cash_open=100) is True


def test_should_not_cancel_while_edge_holds():
    assert should_cancel_remaining(0.02, 0.015, stop_hit=False, minutes_to_cash_open=100) is False
