async def test_different_unit_of_measurement(hass: HomeAssistant) -> None:
    """Test for different unit of measurement."""
    config = {
        "sensor": {
            "platform": "min_max",
            "name": "test",
            "type": "mean",
            "entity_ids": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
        }
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    entity_ids = config["sensor"]["entity_ids"]

    hass.states.async_set(
        entity_ids[0], VALUES[0], {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")

    assert str(float(VALUES[0])) == state.state
    assert state.attributes.get("unit_of_measurement") == UnitOfTemperature.CELSIUS

    hass.states.async_set(
        entity_ids[1],
        VALUES[1],
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT},
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")

    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("unit_of_measurement") == "ERR"

    hass.states.async_set(
        entity_ids[2], VALUES[2], {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")

    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("unit_of_measurement") == "ERR"