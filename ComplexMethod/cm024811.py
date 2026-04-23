def test_time_remaining() -> None:
    """Test get_age."""
    diff = dt_util.now() + timedelta(seconds=0)
    assert dt_util.get_time_remaining(diff) == "0 seconds"
    assert dt_util.get_time_remaining(diff) == "0 seconds"
    assert dt_util.get_time_remaining(diff, precision=2) == "0 seconds"

    diff = dt_util.now() + timedelta(seconds=1)
    assert dt_util.get_time_remaining(diff) == "1 second"

    diff = dt_util.now() - timedelta(seconds=1)
    pytest.raises(ValueError, dt_util.get_time_remaining, diff)

    diff = dt_util.now() + timedelta(seconds=30)
    assert dt_util.get_time_remaining(diff) == "30 seconds"

    diff = dt_util.now() + timedelta(minutes=5)
    assert dt_util.get_time_remaining(diff) == "5 minutes"

    diff = dt_util.now() + timedelta(minutes=1)
    assert dt_util.get_time_remaining(diff) == "1 minute"

    diff = dt_util.now() + timedelta(minutes=300)
    assert dt_util.get_time_remaining(diff) == "5 hours"

    diff = dt_util.now() + timedelta(minutes=320)
    assert dt_util.get_time_remaining(diff) == "5 hours"
    assert dt_util.get_time_remaining(diff, precision=2) == "5 hours 20 minutes"
    assert dt_util.get_time_remaining(diff, precision=3) == "5 hours 20 minutes"

    diff = dt_util.now() + timedelta(minutes=1.6 * 60 * 24)
    assert dt_util.get_time_remaining(diff) == "2 days"
    assert dt_util.get_time_remaining(diff, precision=2) == "1 day 14 hours"
    assert dt_util.get_time_remaining(diff, precision=3) == "1 day 14 hours 24 minutes"
    diff = dt_util.now() - timedelta(minutes=1.6 * 60 * 24)
    pytest.raises(ValueError, dt_util.get_time_remaining, diff)

    diff = dt_util.now() + timedelta(minutes=2 * 60 * 24)
    assert dt_util.get_time_remaining(diff) == "2 days"

    diff = dt_util.now() + timedelta(minutes=32 * 60 * 24)
    assert dt_util.get_time_remaining(diff) == "1 month"
    assert dt_util.get_time_remaining(diff, precision=10) == "1 month 2 days"

    diff = dt_util.now() + timedelta(minutes=32 * 60 * 24 + 1)
    assert dt_util.get_time_remaining(diff, precision=3) == "1 month 2 days 1 minute"

    diff = dt_util.now() + timedelta(minutes=365 * 60 * 24)
    assert dt_util.get_time_remaining(diff) == "1 year"