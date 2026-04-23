async def test_air_quality(hass: HomeAssistant, hk_driver) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = AirQualitySensor(hass, hk_driver, "Air Quality", entity_id, 2, None)
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

    hass.states.async_set(entity_id, "34")
    await hass.async_block_till_done()
    assert acc.char_density.value == 34
    assert acc.char_quality.value == 2

    hass.states.async_set(entity_id, "200")
    await hass.async_block_till_done()
    assert acc.char_density.value == 200
    assert acc.char_quality.value == 5