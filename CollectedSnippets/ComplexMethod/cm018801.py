async def test_device_class(hass: HomeAssistant) -> None:
    """Test device class, which depends on the source entity."""
    assert await async_setup_component(
        hass,
        "sensor",
        {
            "sensor": [
                {
                    # Device class is carried over from source sensor for characteristics which retain unit
                    "platform": "statistics",
                    "name": "test_retain_unit",
                    "entity_id": "sensor.test_monitored",
                    "state_characteristic": "mean",
                    "sampling_size": 20,
                },
                {
                    # Device class is set to None for characteristics with special meaning
                    "platform": "statistics",
                    "name": "test_none",
                    "entity_id": "sensor.test_monitored",
                    "state_characteristic": "count",
                    "sampling_size": 20,
                },
                {
                    # Device class is set to timestamp for datetime characteristics
                    "platform": "statistics",
                    "name": "test_timestamp",
                    "entity_id": "sensor.test_monitored",
                    "state_characteristic": "datetime_oldest",
                    "sampling_size": 20,
                },
                {
                    # Device class is set to None for any source sensor with TOTAL state class
                    "platform": "statistics",
                    "name": "test_source_class_total",
                    "entity_id": "sensor.test_monitored_total",
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
            {
                ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
                ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
                ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
            },
        )
        hass.states.async_set(
            "sensor.test_monitored_total",
            str(value),
            {
                ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.WATT_HOUR,
                ATTR_DEVICE_CLASS: SensorDeviceClass.ENERGY,
                ATTR_STATE_CLASS: SensorStateClass.TOTAL,
            },
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_retain_unit")
    assert state is not None
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TEMPERATURE
    state = hass.states.get("sensor.test_none")
    assert state is not None
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None
    state = hass.states.get("sensor.test_timestamp")
    assert state is not None
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TIMESTAMP
    state = hass.states.get("sensor.test_source_class_total")
    assert state is not None
    assert state.attributes.get(ATTR_DEVICE_CLASS) is None