async def test_device_tracker_test1_awayfurther_than_test2_first_test2(
    hass: HomeAssistant, config_zones
) -> None:
    """Test for tracker ordering."""
    hass.states.async_set(
        "device_tracker.test1", "not_home", {"friendly_name": "test1"}
    )
    hass.states.async_set(
        "device_tracker.test2", "not_home", {"friendly_name": "test2"}
    )

    await async_setup_single_entry(
        hass,
        "zone.home",
        ["device_tracker.test1", "device_tracker.test2"],
        ["zone.work"],
        1,
    )

    hass.states.async_set(
        "device_tracker.test2",
        "not_home",
        {"friendly_name": "test2", "latitude": 40.1, "longitude": 20.1},
    )
    await hass.async_block_till_done()

    # sensor entities
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test2"

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == STATE_UNKNOWN
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN

    entity_base_name = "sensor.home_test2"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "4625254"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN

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
    assert state.state == "4625254"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN