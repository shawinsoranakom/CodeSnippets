async def test_track_sunrise_update_location(hass: HomeAssistant) -> None:
    """Test track the sunrise."""
    # Setup sun component
    hass.config.latitude = 32.87336
    hass.config.longitude = 117.22743

    location = LocationInfo(
        latitude=hass.config.latitude, longitude=hass.config.longitude
    )

    # Get next sunrise
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

    # Mimic sunrise
    with freeze_time(next_rising):
        async_fire_time_changed(hass, next_rising)
        await hass.async_block_till_done()
        assert len(runs) == 1

    # Move!
    with freeze_time(utc_now):
        await hass.config.async_update(latitude=40.755931, longitude=-73.984606)
        await hass.async_block_till_done()

    # update location for astral
    location = LocationInfo(
        latitude=hass.config.latitude, longitude=hass.config.longitude
    )

    # Mimic sunrise
    with freeze_time(next_rising):
        async_fire_time_changed(hass, next_rising)
        await hass.async_block_till_done()
        # Did not increase
        assert len(runs) == 1

    # Get next sunrise
    mod = -1
    while True:
        next_rising = astral.sun.sunrise(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_rising > utc_now:
            break
        mod += 1

    with freeze_time(next_rising):
        # Mimic sunrise at new location
        async_fire_time_changed(hass, next_rising)
        await hass.async_block_till_done()
        assert len(runs) == 2

    unsub()