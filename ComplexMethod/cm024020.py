async def test_remote_scanner_bluetooth_config_entry(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    manufacturer: str,
    source: str,
) -> None:
    """Test the remote scanner gets a bluetooth config entry."""
    manager: HomeAssistantBluetoothManager = _get_manager()

    switchbot_device = generate_ble_device(
        "44:44:33:11:23:45",
        "wohand",
        {},
    )
    switchbot_device_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=[],
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner(source, source, connector, True)
    unsetup = scanner.async_setup()
    assert scanner.source == source
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    cancel = manager.async_register_hass_scanner(
        scanner,
        source_domain="test",
        source_model="test",
        source_config_entry_id=entry.entry_id,
    )
    await hass.async_block_till_done()

    scanner.inject_advertisement(switchbot_device, switchbot_device_adv)
    assert len(scanner.discovered_devices) == 1

    cancel()
    unsetup()

    adapter_entry = hass.config_entries.async_entry_for_domain_unique_id(
        "bluetooth", scanner.source
    )
    assert adapter_entry is not None
    assert adapter_entry.state is ConfigEntryState.LOADED

    dev = device_registry.async_get_device(
        connections={(dr.CONNECTION_BLUETOOTH, scanner.source)}
    )
    assert dev is not None
    assert dev.config_entries == {adapter_entry.entry_id}
    assert dev.manufacturer == manufacturer

    manager.async_remove_scanner(scanner.source)
    await hass.async_block_till_done()
    assert not hass.config_entries.async_entry_for_domain_unique_id(
        "bluetooth", scanner.source
    )