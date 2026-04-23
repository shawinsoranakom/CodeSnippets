async def test_states_non_default_timezone(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test states of sensors in a timezone other than UTC."""
    await hass.config.async_set_time_zone("America/New_York")
    now = dt_util.utc_from_timestamp(1495068856)
    freezer.move_to(now)

    for option in OPTION_TYPES:
        await load_int(hass, option)

    state = hass.states.get("sensor.time")
    assert state.state == "20:54"

    state = hass.states.get("sensor.date")
    assert state.state == "2017-05-17"

    state = hass.states.get("sensor.time_utc")
    assert state.state == "00:54"

    state = hass.states.get("sensor.date_time")
    assert state.state == "2017-05-17, 20:54"

    state = hass.states.get("sensor.date_time_utc")
    assert state.state == "2017-05-18, 00:54"

    state = hass.states.get("sensor.date_time_iso")
    assert state.state == "2017-05-17T20:54:00"

    # Time travel
    now = dt_util.utc_from_timestamp(1602952963.2)
    freezer.move_to(now)
    async_fire_time_changed(hass, now)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.time")
    assert state.state == "12:42"

    state = hass.states.get("sensor.date")
    assert state.state == "2020-10-17"

    state = hass.states.get("sensor.time_utc")
    assert state.state == "16:42"

    state = hass.states.get("sensor.date_time")
    assert state.state == "2020-10-17, 12:42"

    state = hass.states.get("sensor.date_time_utc")
    assert state.state == "2020-10-17, 16:42"

    state = hass.states.get("sensor.date_time_iso")
    assert state.state == "2020-10-17T12:42:00"

    # Change time zone
    await hass.config.async_update(time_zone="Europe/Prague")
    await hass.async_block_till_done()

    state = hass.states.get("sensor.time")
    assert state.state == "18:42"

    state = hass.states.get("sensor.date")
    assert state.state == "2020-10-17"

    state = hass.states.get("sensor.time_utc")
    assert state.state == "16:42"

    state = hass.states.get("sensor.date_time")
    assert state.state == "2020-10-17, 18:42"

    state = hass.states.get("sensor.date_time_utc")
    assert state.state == "2020-10-17, 16:42"

    state = hass.states.get("sensor.date_time_iso")
    assert state.state == "2020-10-17T18:42:00"