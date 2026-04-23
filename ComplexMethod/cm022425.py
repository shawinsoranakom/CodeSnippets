async def test_setting_rising(hass: HomeAssistant) -> None:
    """Test retrieving sun setting and rising."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    with freeze_time(utc_now):
        await async_setup_component(hass, sun.DOMAIN, {sun.DOMAIN: {}})

    await hass.async_block_till_done()
    state = hass.states.get(entity.ENTITY_ID)

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
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_setting > utc_now:
            break
        mod += 1

    assert next_dawn == dt_util.parse_datetime(
        state.attributes[entity.STATE_ATTR_NEXT_DAWN]
    )
    assert next_dusk == dt_util.parse_datetime(
        state.attributes[entity.STATE_ATTR_NEXT_DUSK]
    )
    assert next_midnight == dt_util.parse_datetime(
        state.attributes[entity.STATE_ATTR_NEXT_MIDNIGHT]
    )
    assert next_noon == dt_util.parse_datetime(
        state.attributes[entity.STATE_ATTR_NEXT_NOON]
    )
    assert next_rising == dt_util.parse_datetime(
        state.attributes[entity.STATE_ATTR_NEXT_RISING]
    )
    assert next_setting == dt_util.parse_datetime(
        state.attributes[entity.STATE_ATTR_NEXT_SETTING]
    )