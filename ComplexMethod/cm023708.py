async def test_resolve_period(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    start_time: datetime,
    periods: dict[tuple[str, int], tuple[str, str]],
) -> None:
    """Test resolve_period."""
    assert hass.config.time_zone == "US/Pacific"
    freezer.move_to(start_time)

    now = dt_util.utcnow()

    for period_def, expected_period in periods.items():
        start_t, end_t = resolve_period(
            {"calendar": {"period": period_def[0], "offset": period_def[1]}}
        )
        assert start_t.isoformat() == f"{expected_period[0]}+00:00"
        assert end_t.isoformat() == f"{expected_period[1]}+00:00"

    # Fixed period
    assert resolve_period({}) == (None, None)

    assert resolve_period({"fixed_period": {"end_time": now}}) == (None, now)

    assert resolve_period({"fixed_period": {"start_time": now}}) == (now, None)

    assert resolve_period({"fixed_period": {"end_time": now, "start_time": now}}) == (
        now,
        now,
    )

    # Rolling window
    assert resolve_period(
        {"rolling_window": {"duration": timedelta(hours=1, minutes=25)}}
    ) == (now - timedelta(hours=1, minutes=25), now)

    assert resolve_period(
        {
            "rolling_window": {
                "duration": timedelta(hours=1),
                "offset": timedelta(minutes=-25),
            }
        }
    ) == (now - timedelta(hours=1, minutes=25), now - timedelta(minutes=25))