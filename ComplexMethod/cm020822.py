async def test_tracked_zone_location_is_changed(hass: HomeAssistant) -> None:
    """Test that gps location of the tracked zone is changed."""
    entry = await async_setup_single_entry(
        hass, "zone.home", ["device_tracker.test1"], [], 1
    )

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20.1, "longitude": 10.1},
    )
    await hass.async_block_till_done()

    # check sensor entities before location change
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "2218742"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN

    # change location of tracked zone
    hass.states.async_set(
        "zone.home",
        "zoning",
        {"name": "Home", "latitude": 10, "longitude": 5, "radius": 10},
    )
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    latitude = hass.states.get("zone.home").attributes["latitude"]
    assert latitude == 10
    longitude = hass.states.get("zone.home").attributes["longitude"]
    assert longitude == 5

    # check sensor entities after location change
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"

    entity_base_name = "sensor.home_test1"
    state = hass.states.get(f"{entity_base_name}_distance")
    assert state.state == "1244478"
    state = hass.states.get(f"{entity_base_name}_direction_of_travel")
    assert state.state == STATE_UNKNOWN