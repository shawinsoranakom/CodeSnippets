async def test_device_info_to_link(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test for returning device info with device link information."""
    config_entry = MockConfigEntry(domain="my")
    config_entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        identifiers={("test", "my_device")},
        connections={("mac", "30:31:32:33:34:00")},
        config_entry_id=config_entry.entry_id,
    )
    assert device is not None

    # Source entity registry
    source_entity = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source",
        config_entry=config_entry,
        device_id=device.id,
    )
    await hass.async_block_till_done()
    assert entity_registry.async_get("sensor.test_source") is not None

    result = async_device_info_to_link_from_entity(
        hass, entity_id_or_uuid=source_entity.entity_id
    )
    assert result == {
        "identifiers": {("test", "my_device")},
        "connections": {("mac", "30:31:32:33:34:00")},
    }

    result = async_device_info_to_link_from_device_id(hass, device_id=device.id)
    assert result == {
        "identifiers": {("test", "my_device")},
        "connections": {("mac", "30:31:32:33:34:00")},
    }

    # With a non-existent entity id
    result = async_device_info_to_link_from_entity(
        hass, entity_id_or_uuid="sensor.invalid"
    )
    assert result is None

    # With a non-existent device id
    result = async_device_info_to_link_from_device_id(hass, device_id="abcdefghi")
    assert result is None

    # With a None device id
    result = async_device_info_to_link_from_device_id(hass, device_id=None)
    assert result is None