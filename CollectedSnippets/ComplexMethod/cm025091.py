async def test_track_sunrise(hass: HomeAssistant) -> None:
    """Test track the sunrise."""
    latitude = 32.87336
    longitude = 117.22743

    # Setup sun component
    hass.config.latitude = latitude
    hass.config.longitude = longitude

    location = LocationInfo(
        latitude=hass.config.latitude, longitude=hass.config.longitude
    )

    # Get next sunrise/sunset
    utc_now = datetime(2014, 5, 24, 12, 0, 0, tzinfo=dt_util.UTC)
    utc_today = utc_now.date()

    mod = -1
    while True:
        next_rising = astral.sun.sunrise(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_rising > utc_now:
            break
        mod += 1

    # Track sunrise
    runs = []
    with freeze_time(utc_now):
        unsub = async_track_sunrise(hass, callback(lambda: runs.append(1)))

    offset_runs = []
    offset = timedelta(minutes=30)
    with freeze_time(utc_now):
        unsub2 = async_track_sunrise(
            hass, callback(lambda: offset_runs.append(1)), offset
        )

    # run tests
    with freeze_time(next_rising - offset):
        async_fire_time_changed(hass, next_rising - offset)
        await hass.async_block_till_done()
        assert len(runs) == 0
        assert len(offset_runs) == 0

    with freeze_time(next_rising):
        async_fire_time_changed(hass, next_rising)
        await hass.async_block_till_done()
        assert len(runs) == 1
        assert len(offset_runs) == 0

    with freeze_time(next_rising + offset):
        async_fire_time_changed(hass, next_rising + offset)
        await hass.async_block_till_done()
        assert len(runs) == 1
        assert len(offset_runs) == 1

    unsub()
    unsub2()

    with freeze_time(next_rising + offset):
        async_fire_time_changed(hass, next_rising + offset)
        await hass.async_block_till_done()
        assert len(runs) == 1
        assert len(offset_runs) == 1