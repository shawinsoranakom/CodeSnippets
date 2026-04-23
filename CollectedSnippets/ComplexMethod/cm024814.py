def test_find_next_time_expression_time_dst_chicago() -> None:
    """Test daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)

    def find(dt, hour, minute, second) -> datetime:
        """Call test_find_next_time_expression_time."""
        seconds = dt_util.parse_time_expression(second, 0, 59)
        minutes = dt_util.parse_time_expression(minute, 0, 59)
        hours = dt_util.parse_time_expression(hour, 0, 23)

        local = dt_util.find_next_time_expression_time(dt, seconds, minutes, hours)
        return dt_util.as_utc(local)

    # Entering DST, clocks are rolled forward
    assert dt_util.as_utc(datetime(2021, 3, 15, 2, 30, 0, tzinfo=tz)) == find(
        datetime(2021, 3, 14, 1, 50, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 3, 15, 2, 30, 0, tzinfo=tz)) == find(
        datetime(2021, 3, 14, 3, 50, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 3, 15, 2, 30, 0, tzinfo=tz)) == find(
        datetime(2021, 3, 14, 1, 50, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 3, 14, 3, 30, 0, tzinfo=tz)) == find(
        datetime(2021, 3, 14, 1, 50, 0, tzinfo=tz), 3, 30, 0
    )

    # Leaving DST, clocks are rolled back
    assert dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=0)) == find(
        datetime(2021, 11, 7, 2, 5, 0, tzinfo=tz, fold=0), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz)) == find(
        datetime(2021, 11, 7, 2, 5, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=0)) == find(
        datetime(2021, 11, 7, 2, 5, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=1)) == find(
        datetime(2021, 11, 7, 2, 10, 0, tzinfo=tz), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=1)) == find(
        datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=0), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 11, 8, 2, 30, 0, tzinfo=tz, fold=1)) == find(
        datetime(2021, 11, 7, 2, 55, 0, tzinfo=tz, fold=0), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 11, 7, 4, 30, 0, tzinfo=tz, fold=0)) == find(
        datetime(2021, 11, 7, 2, 55, 0, tzinfo=tz, fold=1), 4, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=1)) == find(
        datetime(2021, 11, 7, 2, 5, 0, tzinfo=tz, fold=1), 2, 30, 0
    )

    assert dt_util.as_utc(datetime(2021, 11, 8, 2, 30, 0, tzinfo=tz)) == find(
        datetime(2021, 11, 7, 2, 55, 0, tzinfo=tz, fold=0), 2, 30, 0
    )