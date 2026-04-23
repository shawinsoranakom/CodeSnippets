async def test_notification_sensor(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, multisensor_6, integration
) -> None:
    """Test binary sensor created from Notification CC."""
    state = hass.states.get(NOTIFICATION_MOTION_BINARY_SENSOR)

    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.MOTION

    state = hass.states.get(TAMPER_SENSOR)

    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.TAMPER

    entity_entry = entity_registry.async_get(TAMPER_SENSOR)

    assert entity_entry
    assert entity_entry.entity_category is EntityCategory.DIAGNOSTIC