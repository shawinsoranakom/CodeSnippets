async def test_no2(hass: HomeAssistant, hk_driver) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality_nitrogen_dioxide"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = NitrogenDioxideSensor(
        hass, hk_driver, "Nitrogen Dioxide Sensor", entity_id, 2, None
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

    hass.states.async_set(entity_id, "30")
    await hass.async_block_till_done()
    assert acc.char_density.value == 30
    assert acc.char_quality.value == 1

    hass.states.async_set(entity_id, "60")
    await hass.async_block_till_done()
    assert acc.char_density.value == 60
    assert acc.char_quality.value == 2

    hass.states.async_set(entity_id, "80")
    await hass.async_block_till_done()
    assert acc.char_density.value == 80
    assert acc.char_quality.value == 3

    hass.states.async_set(entity_id, "90")
    await hass.async_block_till_done()
    assert acc.char_density.value == 90
    assert acc.char_quality.value == 4

    hass.states.async_set(entity_id, "100")
    await hass.async_block_till_done()
    assert acc.char_density.value == 100
    assert acc.char_quality.value == 5