def test_next_events(hass: HomeAssistant) -> None:
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)

    utc_today = utc_now.date()

    location = LocationInfo(
        latitude=hass.config.latitude, longitude=hass.config.longitude
    )

    mod = -1
    while True:
        next_dawn = astral.sun.dawn(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_dawn > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_dusk = astral.sun.dusk(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_dusk > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_midnight = astral.sun.midnight(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_midnight > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_noon = astral.sun.noon(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_noon > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_rising = astral.sun.sunrise(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_rising > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_setting = astral.sun.sunset(
            location.observer, utc_today + timedelta(days=mod)
        )
        if next_setting > utc_now:
            break
        mod += 1

    with freeze_time(utc_now):
        assert next_dawn == sun.get_astral_event_next(hass, "dawn")
        assert next_dusk == sun.get_astral_event_next(hass, "dusk")
        assert next_midnight == sun.get_astral_event_next(hass, "midnight")
        assert next_noon == sun.get_astral_event_next(hass, "noon")
        assert next_rising == sun.get_astral_event_next(hass, SUN_EVENT_SUNRISE)
        assert next_setting == sun.get_astral_event_next(hass, SUN_EVENT_SUNSET)