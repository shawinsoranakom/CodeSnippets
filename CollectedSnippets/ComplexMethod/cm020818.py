async def test_device_tracker_test1_nearest_after_test2_in_ignored_zone(
    hass: HomeAssistant, config_zones
) -> None:
    """Test for tracker states."""
    await hass.async_block_till_done()
    hass.states.async_set(
        "device_tracker.test1", "not_home", {"friendly_name": "test1"}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "device_tracker.test2", "not_home", {"friendly_name": "test2"}
    )
    await hass.async_block_till_done()

    await async_setup_single_entry(
        hass,
        "zone.home",
        ["device_tracker.test1", "device_tracker.test2"],
        ["zone.work"],
        1,
    )

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1, "longitude": 10.1},
    )
    await hass.async_block_till_done()

    # sensor entities
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "2218742"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN

    entity_base_name = "sensor.home_test2"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == STATE_UNKNOWN
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN

    hass.states.async_set(
        "device_tracker.test2",
        "not_home",
        {"friendly_name": "test2", "latitude": 10.1, "longitude": 5.1},
    )
    await hass.async_block_till_done()

    # sensor entities
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test2"

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "2218742"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN

    entity_base_name = "sensor.home_test2"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "989146"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN

    hass.states.async_set(
        "device_tracker.test2",
        "work",
        {"friendly_name": "test2", "latitude": 12.6, "longitude": 7.6},
    )
    await hass.async_block_till_done()

    # sensor entities
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "2218742"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN

    entity_base_name = "sensor.home_test2"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "1364557"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == "away_from"