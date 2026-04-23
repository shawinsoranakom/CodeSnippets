async def test_sensor_defaults_binary(hass: HomeAssistant) -> None:
    """Test the general behavior of the sensor, with binary source sensor."""
    assert await async_setup_component(
        hass,
        "sensor",
        {
            "sensor": [
                {
                    "platform": "statistics",
                    "name": "test",
                    "entity_id": "binary_sensor.test_monitored",
                    "state_characteristic": "count",
                    "sampling_size": 20,
                },
            ]
        },
    )
    await hass.async_block_till_done()

    for value in VALUES_BINARY:
        hass.states.async_set(
            "binary_sensor.test_monitored",
            value,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state is not None
    assert state.state == str(len(VALUES_BINARY))
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    assert state.attributes.get("buffer_usage_ratio") == round(9 / 20, 2)
    assert state.attributes.get("source_value_valid") is True
    assert "age_coverage_ratio" not in state.attributes