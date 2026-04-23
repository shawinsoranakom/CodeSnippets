async def test_bluetooth_rediscover(
    hass: HomeAssistant,
    entry_domain: str,
    entry_discovery_keys: dict[str, tuple[DiscoveryKey, ...]],
    entry_source: str,
) -> None:
    """Test we reinitiate flows when an ignored config entry is removed."""
    mock_bt = [
        {
            "domain": "switchbot",
            "service_data_uuid": "050a021a-0000-1000-8000-00805f9b34fb",
            "connectable": False,
        },
    ]
    with patch(
        "homeassistant.components.bluetooth.async_get_bluetooth", return_value=mock_bt
    ):
        assert await async_setup_component(hass, bluetooth.DOMAIN, {})
        await hass.async_block_till_done()

    assert async_scanner_count(hass, connectable=False) == 0
    switchbot_device_non_connectable = generate_ble_device(
        "44:44:33:11:23:45",
        "wohand",
        {},
    )
    switchbot_device_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=["050a021a-0000-1000-8000-00805f9b34fb"],
        service_data={"050a021a-0000-1000-8000-00805f9b34fb": b"\n\xff"},
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )
    callbacks = []

    def _fake_subscriber(
        service_info: BluetoothServiceInfo,
        change: BluetoothChange,
    ) -> None:
        """Fake subscriber for the BleakScanner."""
        callbacks.append((service_info, change))

    cancel = bluetooth.async_register_callback(
        hass,
        _fake_subscriber,
        {"address": "44:44:33:11:23:45", "connectable": False},
        BluetoothScanningMode.ACTIVE,
    )

    class FakeScanner(BaseHaRemoteScanner):
        def inject_advertisement(
            self, device: BLEDevice, advertisement_data: AdvertisementData
        ) -> None:
            """Inject an advertisement."""
            self._async_on_advertisement(
                device.address,
                advertisement_data.rssi,
                device.name,
                advertisement_data.service_uuids,
                advertisement_data.service_data,
                advertisement_data.manufacturer_data,
                advertisement_data.tx_power,
                {"scanner_specific_data": "test"},
                MONOTONIC_TIME(),
            )

        def clear_all_devices(self) -> None:
            """Clear all devices."""
            self._previous_service_info.clear()

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    non_connectable_scanner = FakeScanner(
        "connectable",
        "connectable",
        connector,
        False,
    )
    unsetup_connectable_scanner = non_connectable_scanner.async_setup()
    cancel_connectable_scanner = _get_manager().async_register_scanner(
        non_connectable_scanner
    )
    with patch.object(hass.config_entries.flow, "async_init") as mock_config_flow:
        non_connectable_scanner.inject_advertisement(
            switchbot_device_non_connectable, switchbot_device_adv
        )
        await hass.async_block_till_done()

        expected_context = {
            "discovery_key": DiscoveryKey(
                domain="bluetooth", key="44:44:33:11:23:45", version=1
            ),
            "source": "bluetooth",
        }
        assert len(mock_config_flow.mock_calls) == 1
        assert mock_config_flow.mock_calls[0][1][0] == "switchbot"
        assert mock_config_flow.mock_calls[0][2]["context"] == expected_context

        hass.config.components.add(entry_domain)
        mock_integration(hass, MockModule(entry_domain))

        entry = MockConfigEntry(
            domain=entry_domain,
            discovery_keys=entry_discovery_keys,
            unique_id="mock-unique-id",
            state=config_entries.ConfigEntryState.LOADED,
            source=entry_source,
        )
        entry.add_to_hass(hass)

        assert (
            async_ble_device_from_address(hass, "44:44:33:11:23:45", False) is not None
        )
        assert async_scanner_count(hass, connectable=False) == 1
        assert len(callbacks) == 1

        assert (
            "44:44:33:11:23:45"
            in non_connectable_scanner.discovered_devices_and_advertisement_data
        )

        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()

        assert (
            async_ble_device_from_address(hass, "44:44:33:11:23:45", False) is not None
        )
        assert async_scanner_count(hass, connectable=False) == 1
        assert len(callbacks) == 1

        assert len(mock_config_flow.mock_calls) == 2
        assert mock_config_flow.mock_calls[1][1][0] == "switchbot"
        assert mock_config_flow.mock_calls[1][2]["context"] == expected_context

    cancel()
    unsetup_connectable_scanner()
    cancel_connectable_scanner()