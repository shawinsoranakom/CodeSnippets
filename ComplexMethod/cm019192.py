async def test_migrate_entity_ids(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    reolink_host: MagicMock,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    original_id: str,
    new_id: str,
    original_dev_id: str,
    new_dev_id: str,
    domain: Platform,
    support_uid: bool,
    support_ch_uid: bool,
) -> None:
    """Test entity ids that need to be migrated."""

    def mock_supported(ch, capability):
        if capability == "UID" and ch is None:
            return support_uid
        if capability == "UID":
            return support_ch_uid
        return True

    reolink_host.channels = [0]
    reolink_host.supported = mock_supported

    dev_entry = device_registry.async_get_or_create(
        identifiers={(DOMAIN, original_dev_id)},
        config_entry_id=config_entry.entry_id,
        disabled_by=None,
    )

    entity_registry.async_get_or_create(
        domain=domain,
        platform=DOMAIN,
        unique_id=original_id,
        config_entry=config_entry,
        suggested_object_id=original_id,
        disabled_by=None,
        device_id=dev_entry.id,
    )

    assert entity_registry.async_get_entity_id(domain, DOMAIN, original_id)
    if original_id != new_id:
        assert entity_registry.async_get_entity_id(domain, DOMAIN, new_id) is None

    assert device_registry.async_get_device(identifiers={(DOMAIN, original_dev_id)})
    if new_dev_id != original_dev_id:
        assert (
            device_registry.async_get_device(identifiers={(DOMAIN, new_dev_id)}) is None
        )

    # setup CH 0 and host entities/device
    with patch("homeassistant.components.reolink.PLATFORMS", [domain]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    if original_id != new_id:
        assert entity_registry.async_get_entity_id(domain, DOMAIN, original_id) is None
    assert entity_registry.async_get_entity_id(domain, DOMAIN, new_id)

    if new_dev_id != original_dev_id:
        assert (
            device_registry.async_get_device(identifiers={(DOMAIN, original_dev_id)})
            is None
        )
    assert device_registry.async_get_device(identifiers={(DOMAIN, new_dev_id)})