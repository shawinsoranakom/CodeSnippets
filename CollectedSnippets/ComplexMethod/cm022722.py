async def test_pm25(hass: HomeAssistant, hk_driver) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality_pm25"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = PM25Sensor(hass, hk_driver, "PM25 Sensor", entity_id, 2, None)
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

    hass.states.async_set(entity_id, "8")
    await hass.async_block_till_done()
    assert acc.char_density.value == 8
    assert acc.char_quality.value == 1

    hass.states.async_set(entity_id, "12")
    await hass.async_block_till_done()
    assert acc.char_density.value == 12
    assert acc.char_quality.value == 2

    hass.states.async_set(entity_id, "23")
    await hass.async_block_till_done()
    assert acc.char_density.value == 23
    assert acc.char_quality.value == 2

    hass.states.async_set(entity_id, "34")
    await hass.async_block_till_done()
    assert acc.char_density.value == 34
    assert acc.char_quality.value == 2

    hass.states.async_set(entity_id, "90")
    await hass.async_block_till_done()
    assert acc.char_density.value == 90
    assert acc.char_quality.value == 4

    hass.states.async_set(entity_id, "200")
    await hass.async_block_till_done()
    assert acc.char_density.value == 200
    assert acc.char_quality.value == 5

    hass.states.async_set(entity_id, "400")
    await hass.async_block_till_done()
    assert acc.char_density.value == 400
    assert acc.char_quality.value == 5