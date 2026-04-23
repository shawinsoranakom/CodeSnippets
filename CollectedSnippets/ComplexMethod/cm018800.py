async def test_percentile(hass: HomeAssistant) -> None:
    """Test correct results for percentile characteristic."""
    assert await async_setup_component(
        hass,
        "sensor",
        {
            "sensor": [
                {
                    "platform": "statistics",
                    "name": "test_percentile_omitted",
                    "entity_id": "sensor.test_monitored",
                    "state_characteristic": "percentile",
                    "sampling_size": 20,
                },
                {
                    "platform": "statistics",
                    "name": "test_percentile_default",
                    "entity_id": "sensor.test_monitored",
                    "state_characteristic": "percentile",
                    "sampling_size": 20,
                    "percentile": 50,
                },
                {
                    "platform": "statistics",
                    "name": "test_percentile_min",
                    "entity_id": "sensor.test_monitored",
                    "state_characteristic": "percentile",
                    "sampling_size": 20,
                    "percentile": 1,
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

    state = hass.states.get("sensor.test_percentile_omitted")
    assert state is not None
    assert state.state == str(9.2)
    state = hass.states.get("sensor.test_percentile_default")
    assert state is not None
    assert state.state == str(9.2)
    state = hass.states.get("sensor.test_percentile_min")
    assert state is not None
    assert state.state == str(2.72)