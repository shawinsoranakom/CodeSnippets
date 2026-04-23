async def test_not_valid_device_class(hass: HomeAssistant) -> None:
    """Test when not valid device class."""
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

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            {
                ATTR_DEVICE_CLASS: SensorDeviceClass.DATE,
            },
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state is not None
    assert state.state == str(round(sum(VALUES_NUMERIC) / len(VALUES_NUMERIC), 2))
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    hass.states.async_set(
        "sensor.test_monitored",
        str(10),
        {
            ATTR_DEVICE_CLASS: "not_exist",
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state is not None
    assert state.state == "10.69"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT