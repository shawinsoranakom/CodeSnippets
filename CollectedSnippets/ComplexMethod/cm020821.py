async def test_tracked_zone_radius_is_changed(hass: HomeAssistant) -> None:
    """Test that radius of the tracked zone is changed."""
    entry = await async_setup_single_entry(
        hass, "zone.home", ["device_tracker.test1"], [], 1
    )

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.10000001, "longitude": 10.1},
    )
    await hass.async_block_till_done()

    # check sensor entities before radius change
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "2218742"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN

    # change radius of tracked zone
    hass.states.async_set(
        "zone.home",
        "zoning",
        {"name": "Home", "latitude": 2.1, "longitude": 1.1, "radius": 110},
    )
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    radius = hass.states.get("zone.home").attributes["radius"]
    assert radius == 110

    # check sensor entities after radius change
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "2218642"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN