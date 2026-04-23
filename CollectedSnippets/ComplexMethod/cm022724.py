async def test_voc(hass: HomeAssistant, hk_driver) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality_volatile_organic_compounds"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = VolatileOrganicCompoundsSensor(
        hass, hk_driver, "Volatile Organic Compounds Sensor", entity_id, 2, None
    )
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

    hass.states.async_set(entity_id, "250")
    await hass.async_block_till_done()
    assert acc.char_density.value == 250
    assert acc.char_quality.value == 1

    hass.states.async_set(entity_id, "500")
    await hass.async_block_till_done()
    assert acc.char_density.value == 500
    assert acc.char_quality.value == 2

    hass.states.async_set(entity_id, "1000")
    await hass.async_block_till_done()
    assert acc.char_density.value == 1000
    assert acc.char_quality.value == 3

    hass.states.async_set(entity_id, "3000")
    await hass.async_block_till_done()
    assert acc.char_density.value == 3000
    assert acc.char_quality.value == 4

    hass.states.async_set(entity_id, "5000")
    await hass.async_block_till_done()
    assert acc.char_density.value == 5000
    assert acc.char_quality.value == 5