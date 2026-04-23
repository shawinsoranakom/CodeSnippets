async def test_sensor_in_range_unknown_state(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test if source is within the range."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_LOWER: "10",
            CONF_UPPER: "20",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    assert await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)
    await hass.async_block_till_done()

    hass.states.async_set(
        "sensor.test_monitored",
        16,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.threshold")

    assert state.attributes[ATTR_ENTITY_ID] == "sensor.test_monitored"
    assert state.attributes[ATTR_SENSOR_VALUE] == 16
    assert state.attributes[ATTR_POSITION] == POSITION_IN_RANGE
    assert state.attributes[ATTR_LOWER] == float(
        config[Platform.BINARY_SENSOR][CONF_LOWER]
    )
    assert state.attributes[ATTR_UPPER] == float(
        config[Platform.BINARY_SENSOR][CONF_UPPER]
    )
    assert state.attributes[ATTR_HYSTERESIS] == 0.0
    assert state.attributes[ATTR_TYPE] == TYPE_RANGE
    assert state.state == STATE_ON

    hass.states.async_set("sensor.test_monitored", STATE_UNKNOWN)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    assert state.attributes[ATTR_POSITION] == POSITION_UNKNOWN
    assert state.state == STATE_UNKNOWN

    hass.states.async_set("sensor.test_monitored", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    assert state.attributes[ATTR_POSITION] == POSITION_UNKNOWN
    assert state.state == STATE_UNKNOWN

    assert "State is not numerical" not in caplog.text