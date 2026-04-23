async def test_not_enough_sensor_value(hass: HomeAssistant) -> None:
    """Test that there is nothing done if not enough values available."""
    config = {
        SENSOR_DOMAIN: {
            "platform": DOMAIN,
            "name": "test_max",
            "type": "max",
            "ignore_non_numeric": True,
            "entities": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
            "state_class": SensorStateClass.MEASUREMENT,
        }
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    entity_ids = config["sensor"]["entities"]

    hass.states.async_set(entity_ids[0], STATE_UNKNOWN)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_max")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("min_entity_id") is None
    assert state.attributes.get("max_entity_id") is None

    hass.states.async_set(entity_ids[1], str(VALUES[1]))
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_max")
    assert state.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]
    assert state.attributes.get("max_entity_id") == entity_ids[1]

    hass.states.async_set(entity_ids[2], STATE_UNKNOWN)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_max")
    assert state.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]
    assert state.attributes.get("max_entity_id") == entity_ids[1]

    hass.states.async_set(entity_ids[1], STATE_UNAVAILABLE)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_max")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("min_entity_id") is None
    assert state.attributes.get("max_entity_id") is None