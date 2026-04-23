async def test_cleanup_combined_with_NVR(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    reolink_host: MagicMock,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test cleanup of the device registry if IPC camera device was combined with the NVR device."""
    reolink_host.channels = [0]
    reolink_host.baichuan.mac_address.return_value = None
    entity_id = f"{TEST_UID}_{TEST_UID_CAM}_record_audio"
    dev_id = f"{TEST_UID}_{TEST_UID_CAM}"
    domain = Platform.SWITCH
    start_identifiers = {
        (DOMAIN, dev_id),
        (DOMAIN, TEST_UID),
        ("OTHER_INTEGRATION", "SOME_ID"),
    }

    dev_entry = device_registry.async_get_or_create(
        identifiers=start_identifiers,
        connections={(CONNECTION_NETWORK_MAC, TEST_MAC)},
        config_entry_id=config_entry.entry_id,
        disabled_by=None,
    )

    entity_registry.async_get_or_create(
        domain=domain,
        platform=DOMAIN,
        unique_id=entity_id,
        config_entry=config_entry,
        suggested_object_id=entity_id,
        disabled_by=None,
        device_id=dev_entry.id,
    )

    assert entity_registry.async_get_entity_id(domain, DOMAIN, entity_id)
    device = device_registry.async_get_device(identifiers={(DOMAIN, dev_id)})
    assert device
    assert device.identifiers == start_identifiers

    # setup CH 0 and host entities/device
    with patch("homeassistant.components.reolink.PLATFORMS", [domain]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert entity_registry.async_get_entity_id(domain, DOMAIN, entity_id)
    device = device_registry.async_get_device(identifiers={(DOMAIN, dev_id)})
    assert device
    assert device.identifiers == {(DOMAIN, dev_id)}
    host_device = device_registry.async_get_device(identifiers={(DOMAIN, TEST_UID)})
    assert host_device
    assert host_device.identifiers == {
        (DOMAIN, TEST_UID),
        ("OTHER_INTEGRATION", "SOME_ID"),
    }