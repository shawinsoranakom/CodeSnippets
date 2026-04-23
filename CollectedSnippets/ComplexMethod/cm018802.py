async def test_state_class(hass: HomeAssistant) -> None:
    """Test state class, which depends on the characteristic configured."""
    assert await async_setup_component(
        hass,
        "sensor",
        {
            "sensor": [
                {
                    # State class is None for datetime characteristics
                    "platform": "statistics",
                    "name": "test_nan",
                    "entity_id": "sensor.test_monitored",
                    "state_characteristic": "datetime_oldest",
                    "sampling_size": 20,
                },
                {
                    # State class is MEASUREMENT for all other characteristics
                    "platform": "statistics",
                    "name": "test_normal",
                    "entity_id": "sensor.test_monitored",
                    "state_characteristic": "count",
                    "sampling_size": 20,
                },
                {
                    # State class is MEASUREMENT, even when the source sensor
                    # is of state class TOTAL
                    "platform": "statistics",
                    "name": "test_total",
                    "entity_id": "sensor.test_monitored_total",
                    "state_characteristic": "count",
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
        hass.states.async_set(
            "sensor.test_monitored_total",
            str(value),
            {
                ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
                ATTR_STATE_CLASS: SensorStateClass.TOTAL,
            },
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_nan")
    assert state is not None
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    state = hass.states.get("sensor.test_normal")
    assert state is not None
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    state = hass.states.get("sensor.test_monitored_total")
    assert state is not None
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.TOTAL
    state = hass.states.get("sensor.test_total")
    assert state is not None
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT