def test_interval_large_integers(interval_type):
    """Check that Interval constraint work with large integers.

    non-regression test for #26648.
    """
    interval = Interval(interval_type, 0, 2, closed="neither")
    assert 2**65 not in interval
    assert 2**128 not in interval
    assert float(2**65) not in interval
    assert float(2**128) not in interval

    interval = Interval(interval_type, 0, 2**128, closed="neither")
    assert 2**65 in interval
    assert 2**128 not in interval
    assert float(2**65) in interval
    assert float(2**128) not in interval

    assert 2**1024 not in interval