async def test_pm10(hass: HomeAssistant, hk_driver) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality_pm10"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = PM10Sensor(hass, hk_driver, "PM10 Sensor", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_density.value == 0
    assert acc.char_quality.value == 0

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert acc.char_density.value == 0
    assert acc.char_quality.value == 0

    hass.states.async_set(entity_id, "54")
    await hass.async_block_till_done()
    assert acc.char_density.value == 54
    assert acc.char_quality.value == 1

    hass.states.async_set(entity_id, "154")
    await hass.async_block_till_done()
    assert acc.char_density.value == 154
    assert acc.char_quality.value == 2

    hass.states.async_set(entity_id, "254")
    await hass.async_block_till_done()
    assert acc.char_density.value == 254
    assert acc.char_quality.value == 3

    hass.states.async_set(entity_id, "354")
    await hass.async_block_till_done()
    assert acc.char_density.value == 354
    assert acc.char_quality.value == 4

    hass.states.async_set(entity_id, "400")
    await hass.async_block_till_done()
    assert acc.char_density.value == 400
    assert acc.char_quality.value == 5