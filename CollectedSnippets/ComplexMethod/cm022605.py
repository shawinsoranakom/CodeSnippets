async def test_dst5(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_tz_info
) -> None:
    """Test DST when end time falls in non-existent hour (1:50am-2:10am)."""
    hass.config.time_zone = "CET"
    dt_util.set_default_time_zone(dt_util.get_time_zone("CET"))
    test_time1 = datetime(2019, 3, 30, 3, 0, 0, tzinfo=dt_util.get_time_zone("CET"))
    test_time2 = datetime(2019, 3, 31, 1, 51, 0, tzinfo=dt_util.get_time_zone("CET"))
    config = {
        "binary_sensor": [
            {"platform": "tod", "name": "Day", "after": "1:50", "before": "2:10"}
        ]
    }
    # Test DST #5:
    # Test the case where the end time does not exist (roll out to the next available time)
    # First test before the sensor is turned on
    entity_id = "binary_sensor.day"
    freezer.move_to(test_time1)
    await async_setup_component(hass, "binary_sensor", config)
    await hass.async_block_till_done()

    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes["after"] == "2019-03-31T01:50:00+01:00"
    assert state.attributes["before"] == "2019-03-31T03:00:00+02:00"
    assert state.attributes["next_update"] == "2019-03-31T01:50:00+01:00"
    assert state.state == STATE_OFF

    # Seconds, test state when sensor is ON but end time has rolled out to next available time.
    freezer.move_to(test_time2)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.attributes["after"] == "2019-03-31T01:50:00+01:00"
    assert state.attributes["before"] == "2019-03-31T03:00:00+02:00"
    assert state.attributes["next_update"] == "2019-03-31T03:00:00+02:00"

    assert state.state == STATE_ON