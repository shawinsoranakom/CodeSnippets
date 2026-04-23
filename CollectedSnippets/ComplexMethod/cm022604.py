async def test_dst1(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_tz_info
) -> None:
    """Test DST when time falls in non-existent hour. Also check 48 hours later."""
    hass.config.time_zone = "CET"
    dt_util.set_default_time_zone(dt_util.get_time_zone("CET"))
    test_time1 = datetime(2019, 3, 30, 3, 0, 0, tzinfo=dt_util.get_time_zone("CET"))
    test_time2 = datetime(2019, 3, 31, 3, 0, 0, tzinfo=dt_util.get_time_zone("CET"))
    config = {
        "binary_sensor": [
            {"platform": "tod", "name": "Day", "after": "2:30", "before": "2:40"}
        ]
    }
    # Test DST #1:
    # after 2019-03-30 03:00 CET the next update should ge scheduled
    # at 2:30am, but on 2019-03-31, that hour does not exist.  That means
    # the start/end will end up happning on the next available second (3am)
    # Essentially, the ToD sensor never turns on that day.
    entity_id = "binary_sensor.day"
    freezer.move_to(test_time1)
    await async_setup_component(hass, "binary_sensor", config)
    await hass.async_block_till_done()

    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes["after"] == "2019-03-31T03:00:00+02:00"
    assert state.attributes["before"] == "2019-03-31T03:00:00+02:00"
    assert state.attributes["next_update"] == "2019-03-31T03:00:00+02:00"
    assert state.state == STATE_OFF

    # But the following day, the sensor should resume it normal operation.
    freezer.move_to(test_time2)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.attributes["after"] == "2019-04-01T02:30:00+02:00"
    assert state.attributes["before"] == "2019-04-01T02:40:00+02:00"
    assert state.attributes["next_update"] == "2019-04-01T02:30:00+02:00"

    assert state.state == STATE_OFF