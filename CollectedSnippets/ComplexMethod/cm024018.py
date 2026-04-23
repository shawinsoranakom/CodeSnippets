async def test_restore_history_remote_adapter(
    hass: HomeAssistant, hass_storage: dict[str, Any], disable_new_discovery_flows
) -> None:
    """Test we can restore history for a remote adapter."""

    data = hass_storage[storage.REMOTE_SCANNER_STORAGE_KEY] = json_loads(
        await async_load_fixture(hass, "bluetooth.remote_scanners", bluetooth.DOMAIN)
    )
    now = time.time()
    timestamps = data["data"]["atom-bluetooth-proxy-ceaac4"][
        "discovered_device_timestamps"
    ]
    for address in timestamps:
        if address != "E3:A5:63:3E:5E:23":
            timestamps[address] = now

    with (
        patch(
            "bluetooth_adapters.systems.linux.LinuxAdapters.history",
            {},
        ),
        patch(
            "bluetooth_adapters.systems.linux.LinuxAdapters.refresh",
        ),
    ):
        assert await async_setup_component(hass, bluetooth.DOMAIN, {})
        await hass.async_block_till_done()

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = BaseHaRemoteScanner(
        "atom-bluetooth-proxy-ceaac4",
        "atom-bluetooth-proxy-ceaac4",
        connector,
        True,
    )
    unsetup = scanner.async_setup()
    cancel = _get_manager().async_register_scanner(scanner)

    assert "EB:0B:36:35:6F:A4" in scanner.discovered_devices_and_advertisement_data
    assert "E3:A5:63:3E:5E:23" not in scanner.discovered_devices_and_advertisement_data
    cancel()
    unsetup()

    scanner = BaseHaRemoteScanner(
        "atom-bluetooth-proxy-ceaac4",
        "atom-bluetooth-proxy-ceaac4",
        connector,
        True,
    )
    unsetup = scanner.async_setup()
    cancel = _get_manager().async_register_scanner(scanner)
    assert "EB:0B:36:35:6F:A4" in scanner.discovered_devices_and_advertisement_data
    assert "E3:A5:63:3E:5E:23" not in scanner.discovered_devices_and_advertisement_data

    cancel()
    unsetup()