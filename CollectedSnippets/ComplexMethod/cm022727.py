async def test_binary(hass: HomeAssistant, hk_driver) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "binary_sensor.opening"

    hass.states.async_set(entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: "opening"})
    await hass.async_block_till_done()

    acc = BinarySensor(hass, hk_driver, "Window Opening", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_detected.value == 0

    hass.states.async_set(entity_id, STATE_ON, {ATTR_DEVICE_CLASS: "opening"})
    await hass.async_block_till_done()
    assert acc.char_detected.value == 1

    hass.states.async_set(entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: "opening"})
    await hass.async_block_till_done()
    assert acc.char_detected.value == 0

    hass.states.async_set(entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: "opening"})
    await hass.async_block_till_done()
    assert acc.char_detected.value == 0

    hass.states.async_set(entity_id, STATE_UNAVAILABLE, {ATTR_DEVICE_CLASS: "opening"})
    await hass.async_block_till_done()
    assert acc.char_detected.value == 0

    hass.states.async_remove(entity_id)
    await hass.async_block_till_done()
    assert acc.char_detected.value == 0