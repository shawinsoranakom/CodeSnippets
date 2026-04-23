async def test_nearest_sensors(hass: HomeAssistant, config_zones) -> None:
    """Test for nearest sensors."""
    await async_setup_single_entry(
        hass, "zone.home", ["device_tracker.test1", "device_tracker.test2"], [], 1
    )

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20, "longitude": 10},
    )
    hass.states.async_set(
        "device_tracker.test2",
        "not_home",
        {"friendly_name": "test2", "latitude": 40, "longitude": 20},
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 15, "longitude": 8},
    )
    hass.states.async_set(
        "device_tracker.test2",
        "not_home",
        {"friendly_name": "test2", "latitude": 45, "longitude": 22},
    )
    await hass.async_block_till_done()

    # sensor entities
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"
    state = hass.states.get("sensor.home_nearest_distance")
    assert state.state == "1615580"
    state = hass.states.get("sensor.home_test1_direction_of_travel")
    assert state.state == "towards"
    state = hass.states.get("sensor.home_test1_distance")
    assert state.state == "1615580"
    state = hass.states.get("sensor.home_test1_direction_of_travel")
    assert state.state == "towards"
    state = hass.states.get("sensor.home_test2_distance")
    assert state.state == "5176048"
    state = hass.states.get("sensor.home_test2_direction_of_travel")
    assert state.state == "away_from"

    # move the far tracker
    hass.states.async_set(
        "device_tracker.test2",
        "not_home",
        {"friendly_name": "test2", "latitude": 40, "longitude": 20},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"
    state = hass.states.get("sensor.home_nearest_distance")
    assert state.state == "1615580"
    state = hass.states.get("sensor.home_nearest_direction_of_travel")
    assert state.state == "towards"
    state = hass.states.get("sensor.home_test1_distance")
    assert state.state == "1615580"
    state = hass.states.get("sensor.home_test1_direction_of_travel")
    assert state.state == "towards"
    state = hass.states.get("sensor.home_test2_distance")
    assert state.state == "4611394"
    state = hass.states.get("sensor.home_test2_direction_of_travel")
    assert state.state == "towards"

    # move the near tracker
    hass.states.async_set(
        "device_tracker.test1",
        "not_home",
        {"friendly_name": "test1", "latitude": 20, "longitude": 10},
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == "test1"
    state = hass.states.get("sensor.home_nearest_distance")
    assert state.state == "2204112"
    state = hass.states.get("sensor.home_nearest_direction_of_travel")
    assert state.state == "away_from"
    state = hass.states.get("sensor.home_test1_distance")
    assert state.state == "2204112"
    state = hass.states.get("sensor.home_test1_direction_of_travel")
    assert state.state == "away_from"
    state = hass.states.get("sensor.home_test2_distance")
    assert state.state == "4611394"
    state = hass.states.get("sensor.home_test2_direction_of_travel")
    assert state.state == "towards"

    # get unknown distance and direction
    hass.states.async_set(
        "device_tracker.test1", "not_home", {"friendly_name": "test1"}
    )
    hass.states.async_set(
        "device_tracker.test2", "not_home", {"friendly_name": "test2"}
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.home_nearest_device")
    assert state.state == STATE_UNKNOWN
    state = hass.states.get("sensor.home_nearest_distance")
    assert state.state == STATE_UNKNOWN
    state = hass.states.get("sensor.home_nearest_direction_of_travel")
    assert state.state == STATE_UNKNOWN
    state = hass.states.get("sensor.home_test1_distance")
    assert state.state == STATE_UNKNOWN
    state = hass.states.get("sensor.home_test1_direction_of_travel")
    assert state.state == STATE_UNKNOWN
    state = hass.states.get("sensor.home_test2_distance")
    assert state.state == STATE_UNKNOWN
    state = hass.states.get("sensor.home_test2_direction_of_travel")
    assert state.state == STATE_UNKNOWN