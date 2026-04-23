async def test_track_sunset(hass: HomeAssistant) -> None:
    """Test track the sunset."""
    latitude = 32.87336
    longitude = 117.22743

    location = LocationInfo(latitude=latitude, longitude=longitude)

    # Setup sun component
    hass.config.latitude = latitude
    hass.config.longitude = longitude

    # Get next sunrise/sunset
    utc_now = datetime(2014, 5, 24, 12, 0, 0, tzinfo=dt_util.UTC)
    utc_today = utc_now.date()

    mod = -1
    while True:
        next_setting = astral.sun.sunset(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_setting > utc_now:
            break
        mod += 1

    # Track sunset
    runs = []
    with freeze_time(utc_now):
        unsub = async_track_sunset(hass, callback(lambda: runs.append(1)))

    offset_runs = []
    offset = timedelta(minutes=30)
    with freeze_time(utc_now):
        unsub2 = async_track_sunset(
            hass, callback(lambda: offset_runs.append(1)), offset
        )

    # Run tests
    with freeze_time(next_setting - offset):
        async_fire_time_changed(hass, next_setting - offset)
        await hass.async_block_till_done()
        assert len(runs) == 0
        assert len(offset_runs) == 0

    with freeze_time(next_setting):
        async_fire_time_changed(hass, next_setting)
        await hass.async_block_till_done()
        assert len(runs) == 1
        assert len(offset_runs) == 0

    with freeze_time(next_setting + offset):
        async_fire_time_changed(hass, next_setting + offset)
        await hass.async_block_till_done()
        assert len(runs) == 1
        assert len(offset_runs) == 1

    unsub()
    unsub2()

    with freeze_time(next_setting + offset):
        async_fire_time_changed(hass, next_setting + offset)
        await hass.async_block_till_done()
        assert len(runs) == 1
        assert len(offset_runs) == 1