async def test_device_info(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Verify device information includes expected details."""
    client = create_mock_client()

    await setup_test_config_entry(hass, hyperion_client=client)

    device_id = get_hyperion_device_id(TEST_SYSINFO_ID, TEST_INSTANCE)

    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    assert device
    assert device.config_entries == {TEST_CONFIG_ENTRY_ID}
    assert device.identifiers == {(DOMAIN, device_id)}
    assert device.manufacturer == HYPERION_MANUFACTURER_NAME
    assert device.model == HYPERION_MODEL_NAME
    assert device.name == TEST_INSTANCE_1["friendly_name"]

    entities_from_device = [
        entry.entity_id
        for entry in er.async_entries_for_device(entity_registry, device.id)
    ]
    assert TEST_ENTITY_ID_1 in entities_from_device