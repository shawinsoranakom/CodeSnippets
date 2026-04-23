async def test_goes_unavailable_dismisses_discovery_and_makes_discoverable(
    hass: HomeAssistant,
) -> None:
    """Test that unavailable will dismiss any active discoveries and make device discoverable again."""
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

    assert len(mock_config_flow.mock_calls) == 1
    assert mock_config_flow.mock_calls[0][1][0] == "switchbot"
    assert mock_config_flow.mock_calls[0][2]["context"] == {
        "discovery_key": DiscoveryKey(
            domain="bluetooth", key="44:44:33:11:23:45", version=1
        ),
        "source": "bluetooth",
    }

    assert async_ble_device_from_address(hass, "44:44:33:11:23:45", False) is not None
    assert async_scanner_count(hass, connectable=False) == 1
    assert len(callbacks) == 1

    assert (
        "44:44:33:11:23:45"
        in non_connectable_scanner.discovered_devices_and_advertisement_data
    )

    unavailable_callbacks: list[BluetoothServiceInfoBleak] = []

    @callback
    def _unavailable_callback(service_info: BluetoothServiceInfoBleak) -> None:
        """Wrong device unavailable callback."""
        nonlocal unavailable_callbacks
        unavailable_callbacks.append(service_info.address)

    cancel_unavailable = async_track_unavailable(
        hass,
        _unavailable_callback,
        switchbot_device_non_connectable.address,
        connectable=False,
    )

    assert async_scanner_count(hass, connectable=False) == 1

    non_connectable_scanner.clear_all_devices()
    assert (
        "44:44:33:11:23:45"
        not in non_connectable_scanner.discovered_devices_and_advertisement_data
    )
    monotonic_now = time.monotonic()
    with (
        patch.object(
            hass.config_entries.flow,
            "async_progress_by_init_data_type",
            return_value=[{"flow_id": "mock_flow_id"}],
        ) as mock_async_progress_by_init_data_type,
        patch.object(hass.config_entries.flow, "async_abort") as mock_async_abort,
        patch_bluetooth_time(
            monotonic_now + FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS,
        ),
    ):
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
        )
    await hass.async_block_till_done()
    assert "44:44:33:11:23:45" in unavailable_callbacks

    assert len(mock_async_progress_by_init_data_type.mock_calls) == 1
    assert mock_async_abort.mock_calls[0][1][0] == "mock_flow_id"

    # Test that if the device comes back online, it can be discovered again
    with patch.object(hass.config_entries.flow, "async_init") as mock_config_flow:
        new_switchbot_device_adv = generate_advertisement_data(
            local_name="wohand",
            service_uuids=["050a021a-0000-1000-8000-00805f9b34fb"],
            service_data={"050a021a-0000-1000-8000-00805f9b34fb": b"\n\xff"},
            manufacturer_data={1: b"\x01"},
            rssi=-60,
        )
        non_connectable_scanner.inject_advertisement(
            switchbot_device_non_connectable, new_switchbot_device_adv
        )
        await hass.async_block_till_done()

    assert (
        "44:44:33:11:23:45"
        in non_connectable_scanner.discovered_devices_and_advertisement_data
    )
    assert len(mock_config_flow.mock_calls) == 1
    assert mock_config_flow.mock_calls[0][1][0] == "switchbot"
    assert mock_config_flow.mock_calls[0][2]["context"] == {
        "discovery_key": DiscoveryKey(
            domain="bluetooth", key="44:44:33:11:23:45", version=1
        ),
        "source": "bluetooth",
    }

    cancel_unavailable()

    cancel()
    unsetup_connectable_scanner()
    cancel_connectable_scanner()