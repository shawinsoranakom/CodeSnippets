def test_round_time() -> None:
    """Test lower-precision time rounded."""

    # hours
    assert _round_time(1, 10, 30) == (1, 0, 0)
    assert _round_time(1, 48, 30) == (2, 0, 0)
    assert _round_time(2, 25, 30) == (2, 30, 0)

    # minutes
    assert _round_time(0, 1, 10) == (0, 1, 0)
    assert _round_time(0, 1, 48) == (0, 2, 0)
    assert _round_time(0, 2, 25) == (0, 2, 30)

    # seconds
    assert _round_time(0, 0, 6) == (0, 0, 6)
    assert _round_time(0, 0, 15) == (0, 0, 10)
    assert _round_time(0, 0, 58) == (0, 1, 0)
    assert _round_time(0, 0, 25) == (0, 0, 20)
    assert _round_time(0, 0, 35) == (0, 0, 30)