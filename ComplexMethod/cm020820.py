async def test_tracked_zone_is_removed(hass: HomeAssistant) -> None:
    """Test that tracked zone is removed."""
    await async_setup_single_entry(hass, "zone.home", ["device_tracker.test1"], [], 1)

    hass.states.async_set(
        "device_tracker.test1",
        "home",
        {"friendly_name": "test1", "latitude": 2.1, "longitude": 1.1},
    )
    await hass.async_block_till_done()

    # check sensor entities
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "0"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == "arrived"

    # remove tracked zone and move tracked entity
    assert hass.states.async_remove("zone.home")
    hass.states.async_set(
        "device_tracker.test1",
        "home",
        {"friendly_name": "test1", "latitude": 2.2, "longitude": 1.2},
    )
    await hass.async_block_till_done()

    # check sensor entities
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == STATE_UNKNOWN

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == STATE_UNAVAILABLE
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNAVAILABLE