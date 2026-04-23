async def test_first_available_sensor(hass: HomeAssistant) -> None:
    """Test the first available sensor."""
    config = {
        SENSOR_DOMAIN: {
            "platform": DOMAIN,
            "name": "test_first_available",
            "type": "first_available",
            "entities": ["sensor.test_1", "sensor.test_2", "sensor.test_3"],
            "unique_id": "very_unique_id_first_available_sensor",
            "ignore_non_numeric": True,
        }
    }

    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()

    entity_ids = config["sensor"]["entities"]

    # Ensure that while sensor states are being set
    # the group will always point to the first available sensor.

    for entity_id, value in dict(zip(entity_ids, VALUES, strict=False)).items():
        hass.states.async_set(entity_id, value)
        await hass.async_block_till_done()
        state = hass.states.get("sensor.test_first_available")
        assert str(float(VALUES[0])) == state.state
        assert entity_ids[0] == state.attributes.get("first_available_entity_id")

    # If the second sensor of the group becomes unavailable
    # then the first one should still be taken.

    hass.states.async_set(entity_ids[1], STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_first_available")
    assert str(float(VALUES[0])) == state.state
    assert entity_ids[0] == state.attributes.get("first_available_entity_id")

    # If the first sensor of the group becomes now unavailable
    # then the third one should be taken.

    hass.states.async_set(entity_ids[0], STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_first_available")
    assert str(float(VALUES[2])) == state.state
    assert entity_ids[2] == state.attributes.get("first_available_entity_id")

    # If all sensors of the group become unavailable
    # then the group should also be unavailable.

    hass.states.async_set(entity_ids[2], STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_first_available")
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get("first_available_entity_id") is None