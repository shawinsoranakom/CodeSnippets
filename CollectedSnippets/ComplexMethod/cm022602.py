async def test_norwegian_case_summer(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_tz_info
) -> None:
    """Test location in Norway where the sun doesn't set in summer."""
    hass.config.latitude = 69.6
    hass.config.longitude = 18.8
    hass.config.elevation = 10.0

    test_time = datetime(2010, 6, 1, tzinfo=hass_tz_info)

    sunrise = dt_util.as_local(
        get_astral_event_next(hass, "sunrise", dt_util.as_utc(test_time))
    )
    sunset = dt_util.as_local(
        get_astral_event_next(hass, "sunset", dt_util.as_utc(sunrise))
    )
    config = {
        "binary_sensor": [
            {
                "platform": "tod",
                "name": "Day",
                "after": "sunrise",
                "before": "sunset",
            }
        ]
    }
    entity_id = "binary_sensor.day"
    freezer.move_to(test_time)
    await async_setup_component(hass, "binary_sensor", config)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    freezer.move_to(sunrise + timedelta(seconds=-1))
    async_fire_time_changed(hass, dt_util.utcnow())
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