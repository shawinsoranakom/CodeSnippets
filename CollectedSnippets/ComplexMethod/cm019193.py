async def test_cleanup_mac_connection(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    reolink_host: MagicMock,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test cleanup of the MAC of a IPC which was set to the MAC of the host."""
    reolink_host.channels = [0]
    reolink_host.baichuan.mac_address.return_value = None
    entity_id = f"{TEST_UID}_{TEST_UID_CAM}_record_audio"
    dev_id = f"{TEST_UID}_{TEST_UID_CAM}"
    domain = Platform.SWITCH

    dev_entry = device_registry.async_get_or_create(
        identifiers={(DOMAIN, dev_id), ("OTHER_INTEGRATION", "SOME_ID")},
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
    assert device.connections == {(CONNECTION_NETWORK_MAC, TEST_MAC)}

    # setup CH 0 and host entities/device
    with patch("homeassistant.components.reolink.PLATFORMS", [domain]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert entity_registry.async_get_entity_id(domain, DOMAIN, entity_id)
    device = device_registry.async_get_device(identifiers={(DOMAIN, dev_id)})
    assert device
    assert device.connections == set()