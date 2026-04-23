def test_interval_range(interval_type):
    """Check the range of values depending on closed."""
    interval = Interval(interval_type, -2, 2, closed="left")
    assert -2 in interval
    assert 2 not in interval

    interval = Interval(interval_type, -2, 2, closed="right")
    assert -2 not in interval
    assert 2 in interval

    interval = Interval(interval_type, -2, 2, closed="both")
    assert -2 in interval
    assert 2 in interval

    interval = Interval(interval_type, -2, 2, closed="neither")
    assert -2 not in interval
    assert 2 not in interval