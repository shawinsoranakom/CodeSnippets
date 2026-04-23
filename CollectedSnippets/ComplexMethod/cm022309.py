async def test_sensor_removed(hass: HomeAssistant, mock_bridge_v1: Mock) -> None:
    """Test if 2nd update has removed sensor."""
    mock_bridge_v1.mock_sensor_responses.append(SENSOR_RESPONSE)

    await setup_platform(
        hass, mock_bridge_v1, [Platform.BINARY_SENSOR, Platform.SENSOR]
    )
    assert len(mock_bridge_v1.mock_requests) == 1
    assert len(hass.states.async_all()) == 7

    mock_bridge_v1.mock_sensor_responses.clear()
    keys = ("1", "2", "3")
    mock_bridge_v1.mock_sensor_responses.append({k: SENSOR_RESPONSE[k] for k in keys})

    # Force updates to run again
    await mock_bridge_v1.sensor_manager.coordinator.async_refresh()

    # To flush out the service call to update the group
    await hass.async_block_till_done()

    assert len(mock_bridge_v1.mock_requests) == 2
    assert len(hass.states.async_all()) == 3

    sensor = hass.states.get("binary_sensor.living_room_sensor_motion")
    assert sensor is not None

    removed_sensor = hass.states.get("binary_sensor.kitchen_sensor_motion")
    assert removed_sensor is None