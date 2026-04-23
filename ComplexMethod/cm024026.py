async def test_async_step_integration_discovery_remote_adapter(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    area_registry: ar.AreaRegistry,
) -> None:
    """Test remote adapter configuration via integration discovery."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeRemoteScanner("esp32", "esp32", connector, True)
    manager = _get_manager()
    area_entry = area_registry.async_get_or_create("test")
    cancel_scanner = manager.async_register_scanner(scanner)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("test", "BB:BB:BB:BB:BB:BB")},
        suggested_area=area_entry.id,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
        data={
            CONF_SOURCE: scanner.source,
            CONF_SOURCE_DOMAIN: "test",
            CONF_SOURCE_MODEL: "test",
            CONF_SOURCE_CONFIG_ENTRY_ID: entry.entry_id,
            CONF_SOURCE_DEVICE_ID: device_entry.id,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "esp32"
    assert result["data"] == {
        CONF_SOURCE: scanner.source,
        CONF_SOURCE_DOMAIN: "test",
        CONF_SOURCE_MODEL: "test",
        CONF_SOURCE_CONFIG_ENTRY_ID: entry.entry_id,
        CONF_SOURCE_DEVICE_ID: device_entry.id,
    }
    await hass.async_block_till_done()

    new_entry_id: str = result["result"].entry_id
    new_entry = hass.config_entries.async_get_entry(new_entry_id)
    assert new_entry is not None
    assert new_entry.state is config_entries.ConfigEntryState.LOADED

    ble_device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_BLUETOOTH, scanner.source)}
    )
    assert ble_device_entry is not None
    assert ble_device_entry.via_device_id == device_entry.id
    assert ble_device_entry.area_id == area_entry.id

    await hass.config_entries.async_unload(new_entry.entry_id)
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    cancel_scanner()
    await hass.async_block_till_done()