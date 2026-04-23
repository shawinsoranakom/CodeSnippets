async def test_async_track_time_change(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test tracking time change."""
    none_runs = []
    wildcard_runs = []
    specific_runs = []

    now = dt_util.utcnow()

    time_that_will_not_match_right_away = datetime(
        now.year + 1, 5, 24, 11, 59, 55, tzinfo=dt_util.UTC
    )
    freezer.move_to(time_that_will_not_match_right_away)

    unsub = async_track_time_change(
        hass,
        # pylint: disable-next=unnecessary-lambda
        callback(lambda x: none_runs.append(x)),
    )
    unsub_utc = async_track_utc_time_change(
        hass,
        # pylint: disable-next=unnecessary-lambda
        callback(lambda x: specific_runs.append(x)),
        second=[0, 30],
    )
    unsub_wildcard = async_track_time_change(
        hass,
        # pylint: disable-next=unnecessary-lambda
        callback(lambda x: wildcard_runs.append(x)),
        second="*",
        minute="*",
        hour="*",
    )

    async_fire_time_changed(
        hass, datetime(now.year + 1, 5, 24, 12, 0, 0, 999999, tzinfo=dt_util.UTC)
    )
    await hass.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 1
    assert len(none_runs) == 1

    async_fire_time_changed(
        hass, datetime(now.year + 1, 5, 24, 12, 0, 15, 999999, tzinfo=dt_util.UTC)
    )
    await hass.async_block_till_done()
    assert len(specific_runs) == 1
    assert len(wildcard_runs) == 2
    assert len(none_runs) == 2

    async_fire_time_changed(
        hass, datetime(now.year + 1, 5, 24, 12, 0, 30, 999999, tzinfo=dt_util.UTC)
    )
    await hass.async_block_till_done()
    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 3
    assert len(none_runs) == 3

    unsub()
    unsub_utc()
    unsub_wildcard()

    async_fire_time_changed(
        hass, datetime(now.year + 1, 5, 24, 12, 0, 30, 999999, tzinfo=dt_util.UTC)
    )
    await hass.async_block_till_done()
    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 3
    assert len(none_runs) == 3