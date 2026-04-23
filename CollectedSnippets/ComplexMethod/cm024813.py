def test_find_next_time_expression_time_dst() -> None:
    """Test daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("Europe/Vienna")
    dt_util.set_default_time_zone(tz)

    def find(dt, hour, minute, second) -> datetime:
        """Call test_find_next_time_expression_time."""
        seconds = dt_util.parse_time_expression(second, 0, 59)
        minutes = dt_util.parse_time_expression(minute, 0, 59)
        hours = dt_util.parse_time_expression(hour, 0, 23)

        local = dt_util.find_next_time_expression_time(dt, seconds, minutes, hours)
        return dt_util.as_utc(local)

    # Entering DST, clocks are rolled forward
    assert dt_util.as_utc(datetime(2018, 3, 26, 2, 30, 0, tzinfo=tz)) == find(
        datetime(2018, 3, 25, 1, 50, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2018, 3, 26, 2, 30, 0, tzinfo=tz)) == find(
        datetime(2018, 3, 25, 3, 50, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2018, 3, 26, 2, 30, 0, tzinfo=tz)) == find(
        datetime(2018, 3, 26, 1, 50, 0, tzinfo=tz), 2, 30, 0
    )

    # Leaving DST, clocks are rolled back
    assert dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=0)) == find(
        datetime(2018, 10, 28, 2, 5, 0, tzinfo=tz, fold=0), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=0)) == find(
        datetime(2018, 10, 28, 2, 5, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=1)) == find(
        datetime(2018, 10, 28, 2, 55, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=1)) == find(
        datetime(2018, 10, 28, 2, 55, 0, tzinfo=tz, fold=0), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2018, 10, 28, 4, 30, 0, tzinfo=tz, fold=0)) == find(
        datetime(2018, 10, 28, 2, 55, 0, tzinfo=tz, fold=1), 4, 30, 0
    )

    assert dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=1)) == find(
        datetime(2018, 10, 28, 2, 5, 0, tzinfo=tz, fold=1), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=1)) == find(
        datetime(2018, 10, 28, 2, 55, 0, tzinfo=tz, fold=0), 2, 30, 0
    )