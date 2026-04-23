async def test_co2(hass: HomeAssistant, hk_driver) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "sensor.co2"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = CarbonDioxideSensor(hass, hk_driver, "CO2", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_level.value == 0
    assert acc.char_peak.value == 0
    assert acc.char_detected.value == 0

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert acc.char_level.value == 0
    assert acc.char_peak.value == 0
    assert acc.char_detected.value == 0

    value = 1100
    assert value > THRESHOLD_CO2
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    assert acc.char_level.value == 1100
    assert acc.char_peak.value == 1100
    assert acc.char_detected.value == 1

    value = 800
    assert value < THRESHOLD_CO2
    hass.states.async_set(entity_id, str(value))
    await hass.async_block_till_done()
    assert acc.char_level.value == 800
    assert acc.char_peak.value == 1100
    assert acc.char_detected.value == 0