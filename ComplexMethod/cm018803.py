async def test_unitless_source_sensor(hass: HomeAssistant) -> None:
    """Statistics for a unitless source sensor should never have a unit."""
    assert await async_setup_component(
        hass,
        "sensor",
        {
            "sensor": [
                {
                    "platform": "statistics",
                    "name": "test_unitless_1",
                    "entity_id": "sensor.test_monitored_unitless",
                    "state_characteristic": "count",
                    "sampling_size": 20,
                },
                {
                    "platform": "statistics",
                    "name": "test_unitless_2",
                    "entity_id": "sensor.test_monitored_unitless",
                    "state_characteristic": "mean",
                    "sampling_size": 20,
                },
                {
                    "platform": "statistics",
                    "name": "test_unitless_3",
                    "entity_id": "sensor.test_monitored_unitless",
                    "state_characteristic": "change_second",
                    "sampling_size": 20,
                },
                {
                    "platform": "statistics",
                    "name": "test_unitless_4",
                    "entity_id": "binary_sensor.test_monitored_unitless",
                    "state_characteristic": "count",
                    "sampling_size": 20,
                },
                {
                    "platform": "statistics",
                    "name": "test_unitless_5",
                    "entity_id": "binary_sensor.test_monitored_unitless",
                    "state_characteristic": "mean",
                    "sampling_size": 20,
                },
            ]
        },
    )
    await hass.async_block_till_done()

    for value_numeric in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored_unitless",
            str(value_numeric),
        )
    for value_binary in VALUES_BINARY:
        hass.states.async_set(
            "binary_sensor.test_monitored_unitless",
            str(value_binary),
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_unitless_1")
    assert state and state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    state = hass.states.get("sensor.test_unitless_2")
    assert state and state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    state = hass.states.get("sensor.test_unitless_3")
    assert state and state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    state = hass.states.get("sensor.test_unitless_4")
    assert state and state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None
    state = hass.states.get("sensor.test_unitless_5")
    assert state and state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "%"