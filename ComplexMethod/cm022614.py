async def test_device_info(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Verify device information includes expected details."""
    entry = await setup_mock_motioneye_config_entry(hass)

    device_identifier = get_motioneye_device_identifier(entry.entry_id, TEST_CAMERA_ID)

    device = device_registry.async_get_device(identifiers={device_identifier})
    assert device
    assert device.config_entries == {TEST_CONFIG_ENTRY_ID}
    assert device.identifiers == {device_identifier}
    assert device.manufacturer == MOTIONEYE_MANUFACTURER
    assert device.model == MOTIONEYE_MANUFACTURER
    assert device.name == TEST_CAMERA_NAME

    entities_from_device = [
        entry.entity_id
        for entry in er.async_entries_for_device(entity_registry, device.id)
    ]
    assert TEST_CAMERA_ENTITY_ID in entities_from_device