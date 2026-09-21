import pytest

from seal.signal import compute_spread, is_event_window, parent_side


def test_compute_spread():
    assert compute_spread(110, 100) == pytest.approx(0.10)
    assert compute_spread(90, 100) == pytest.approx(-0.10)


def test_compute_spread_rejects_nonpositive_cash_close():
    with pytest.raises(ValueError):
        compute_spread(100, 0)


def test_is_event_window():
    dates = frozenset({"2026-01-29"})
    assert is_event_window("2026-01-29", dates) is True
    assert is_event_window("2026-01-30", dates) is False


def test_parent_side_below_threshold_is_none():
    assert parent_side(0.01, 0.015, is_event=False) is None


def test_parent_side_event_window_trades_with_move():
    assert parent_side(0.02, 0.015, is_event=True) == "long"
    assert parent_side(-0.02, 0.015, is_event=True) == "short"


def test_parent_side_no_event_fades_the_move():
    assert parent_side(0.02, 0.015, is_event=False) == "short"
    assert parent_side(-0.02, 0.015, is_event=False) == "long"
