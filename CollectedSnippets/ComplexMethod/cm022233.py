async def test_sensor_lower(
    hass: HomeAssistant,
    vals: list[float | str | None],
    expected_position: str,
    expected_state: str,
) -> None:
    """Test if source is below threshold."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_LOWER: "15",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    assert await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.threshold")
    assert state.attributes[ATTR_ENTITY_ID] == "sensor.test_monitored"
    assert state.attributes[ATTR_LOWER] == float(
        config[Platform.BINARY_SENSOR][CONF_LOWER]
    )
    assert state.attributes[ATTR_HYSTERESIS] == 0.0
    assert state.attributes[ATTR_TYPE] == TYPE_LOWER

    for val in vals:
        hass.states.async_set("sensor.test_monitored", val)
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    assert state.attributes[ATTR_POSITION] == expected_position
    assert state.state == expected_state