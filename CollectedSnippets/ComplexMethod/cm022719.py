async def test_temperature(hass: HomeAssistant, hk_driver) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.temperature"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = TemperatureSensor(hass, hk_driver, "Temperature", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_temp.value == 0.0
    for key, value in PROP_CELSIUS.items():
        assert acc.char_temp.properties[key] == value

    hass.states.async_set(
        entity_id, STATE_UNKNOWN, {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()
    assert acc.char_temp.value == 0.0

    hass.states.async_set(
        entity_id, "20", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()
    assert acc.char_temp.value == 20

    hass.states.async_set(
        entity_id, "0", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    )
    await hass.async_block_till_done()
    assert acc.char_temp.value == 0

    # The UOM changes, the accessory should reload itself
    with patch.object(acc, "async_reload") as mock_reload:
        hass.states.async_set(
            entity_id, "75.2", {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT}
        )
        await hass.async_block_till_done()
        assert mock_reload.called