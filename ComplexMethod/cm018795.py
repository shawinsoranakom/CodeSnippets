async def test_sensor_defaults_numeric(hass: HomeAssistant) -> None:
    """Test the general behavior of the sensor, with numeric source sensor."""
    assert await async_setup_component(
        hass,
        "sensor",
        {
            "sensor": [
                {
                    "platform": "statistics",
                    "name": "test",
                    "entity_id": "sensor.test_monitored",
                    "state_characteristic": "mean",
                    "sampling_size": 20,
                },
            ]
        },
    )
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state is not None
    assert state.state == str(round(sum(VALUES_NUMERIC) / len(VALUES_NUMERIC), 2))
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    assert state.attributes.get("buffer_usage_ratio") == round(9 / 20, 2)
    assert state.attributes.get("source_value_valid") is True
    assert "age_coverage_ratio" not in state.attributes
    # Source sensor turns unavailable, then available with valid value,
    # statistics sensor should follow
    state = hass.states.get("sensor.test")
    hass.states.async_set(
        "sensor.test_monitored",
        STATE_UNAVAILABLE,
    )
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    assert new_state is not None
    assert new_state.state == STATE_UNAVAILABLE
    assert new_state.attributes.get("source_value_valid") is None
    hass.states.async_set(
        "sensor.test_monitored",
        "0",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    new_mean = round(sum(VALUES_NUMERIC) / (len(VALUES_NUMERIC) + 1), 2)
    assert new_state is not None
    assert new_state.state == str(new_mean)
    assert (
        new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    )
    assert new_state.attributes.get("buffer_usage_ratio") == round(10 / 20, 2)
    assert new_state.attributes.get("source_value_valid") is True

    # Source sensor has a nonnumerical state, unit and state should not change
    state = hass.states.get("sensor.test")
    hass.states.async_set("sensor.test_monitored", "beer", {})
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    assert new_state is not None
    assert new_state.state == str(new_mean)
    assert (
        new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    )
    assert new_state.attributes.get("source_value_valid") is False

    # Source sensor has the STATE_UNKNOWN state, unit and state should not change
    state = hass.states.get("sensor.test")
    hass.states.async_set("sensor.test_monitored", STATE_UNKNOWN, {})
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    assert new_state is not None
    assert new_state.state == str(new_mean)
    assert (
        new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    )
    assert new_state.attributes.get("source_value_valid") is False

    # Source sensor is removed, unit and state should not change
    # This is equal to a None value being published
    hass.states.async_remove("sensor.test_monitored")
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    assert new_state is not None
    assert new_state.state == str(new_mean)
    assert (
        new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    )
    assert new_state.attributes.get("source_value_valid") is False