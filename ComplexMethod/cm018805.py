async def test_sensor_unit_gets_removed(hass: HomeAssistant) -> None:
    """Test when input lose its unit of measurement."""
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
                    "sampling_size": 10,
                },
            ]
        },
    )
    await hass.async_block_till_done()

    input_attributes = {
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
        ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
    }

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            input_attributes,
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state is not None
    assert state.state == str(round(sum(VALUES_NUMERIC) / len(VALUES_NUMERIC), 2))
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TEMPERATURE
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    hass.states.async_set(
        "sensor.test_monitored",
        str(VALUES_NUMERIC[0]),
        {
            ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state is not None
    assert state.state == "11.39"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    # Temperature device class is not valid with no unit of measurement
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            input_attributes,
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state is not None
    assert state.state == "11.39"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TEMPERATURE
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT