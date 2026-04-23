async def test_sun_offset(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_tz_info
) -> None:
    """Test sun event with offset."""
    test_time = datetime(2019, 1, 12, tzinfo=hass_tz_info)
    sunrise = dt_util.as_local(
        get_astral_event_date(hass, "sunrise", dt_util.as_utc(test_time))
        + timedelta(hours=-1, minutes=-30)
    )
    sunset = dt_util.as_local(
        get_astral_event_date(hass, "sunset", dt_util.as_utc(test_time))
        + timedelta(hours=1, minutes=30)
    )
    config = {
        "binary_sensor": [
            {
                "platform": "tod",
                "name": "Day",
                "after": "sunrise",
                "after_offset": "-1:30",
                "before": "sunset",
                "before_offset": "1:30",
            }
        ]
    }
    entity_id = "binary_sensor.day"
    freezer.move_to(sunrise + timedelta(seconds=-1))
    await async_setup_component(hass, "binary_sensor", config)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    freezer.move_to(sunrise)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    freezer.move_to(sunrise + timedelta(seconds=1))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    freezer.move_to(sunset + timedelta(seconds=-1))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    await hass.async_block_till_done()

    freezer.move_to(sunset)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    freezer.move_to(sunset + timedelta(seconds=1))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    test_time = test_time + timedelta(days=1)
    sunrise = dt_util.as_local(
        get_astral_event_date(hass, "sunrise", dt_util.as_utc(test_time))
        + timedelta(hours=-1, minutes=-30)
    )
    freezer.move_to(sunrise)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON