async def test_new_sensor_discovered(hass: HomeAssistant, mock_bridge_v1: Mock) -> None:
    """Test if 2nd update has a new sensor."""
    mock_bridge_v1.mock_sensor_responses.append(SENSOR_RESPONSE)

    await setup_platform(
        hass, mock_bridge_v1, [Platform.BINARY_SENSOR, Platform.SENSOR]
    )
    assert len(mock_bridge_v1.mock_requests) == 1
    assert len(hass.states.async_all()) == 7

    new_sensor_response = dict(SENSOR_RESPONSE)
    new_sensor_response.update(
        {
            "9": PRESENCE_SENSOR_3_PRESENT,
            "10": LIGHT_LEVEL_SENSOR_3,
            "11": TEMPERATURE_SENSOR_3,
        }
    )

    mock_bridge_v1.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    await mock_bridge_v1.sensor_manager.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(mock_bridge_v1.mock_requests) == 2
    assert len(hass.states.async_all()) == 10

    presence = hass.states.get("binary_sensor.bedroom_sensor_motion")
    assert presence is not None
    assert presence.state == "on"
    temperature = hass.states.get("sensor.bedroom_sensor_temperature")
    assert temperature is not None
    assert temperature.state == "17.75"