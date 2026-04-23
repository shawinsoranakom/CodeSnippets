async def test_motion_uses_bool(hass: HomeAssistant, hk_driver) -> None:
    """Test if accessory is updated after state change."""
    entity_id = "binary_sensor.motion"

    hass.states.async_set(
        entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION}
    )
    await hass.async_block_till_done()

    acc = BinarySensor(hass, hk_driver, "Motion Sensor", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_detected.value is False

    hass.states.async_set(
        entity_id, STATE_ON, {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION}
    )
    await hass.async_block_till_done()
    assert acc.char_detected.value is True

    hass.states.async_set(
        entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION}
    )
    await hass.async_block_till_done()
    assert acc.char_detected.value is False

    hass.states.async_set(
        entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION}
    )
    await hass.async_block_till_done()
    assert acc.char_detected.value is False

    hass.states.async_set(
        entity_id,
        STATE_UNAVAILABLE,
        {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOTION},
    )
    await hass.async_block_till_done()
    assert acc.char_detected.value is False

    hass.states.async_remove(entity_id)
    await hass.async_block_till_done()
    assert acc.char_detected.value is False