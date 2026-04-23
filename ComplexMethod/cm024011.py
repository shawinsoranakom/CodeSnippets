async def test_goes_unavailable_connectable_only_and_recovers(
    hass: HomeAssistant,
) -> None:
    """Test all connectable scanners go unavailable, and than recover when there is a non-connectable scanner."""
    assert await async_setup_component(hass, bluetooth.DOMAIN, {})
    await hass.async_block_till_done()

    assert async_scanner_count(hass, connectable=True) == 0
    assert async_scanner_count(hass, connectable=False) == 0
    switchbot_device_connectable = generate_ble_device(
        "44:44:33:11:23:45",
        "wohand",
        {},
    )
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
        {"address": "44:44:33:11:23:45", "connectable": True},
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

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    connectable_scanner = FakeScanner(
        "connectable",
        "connectable",
        connector,
        True,
    )
    unsetup_connectable_scanner = connectable_scanner.async_setup()
    cancel_connectable_scanner = _get_manager().async_register_scanner(
        connectable_scanner
    )
    connectable_scanner.inject_advertisement(
        switchbot_device_connectable, switchbot_device_adv
    )
    assert async_ble_device_from_address(hass, "44:44:33:11:23:45") is not None
    assert async_scanner_count(hass, connectable=True) == 1
    assert len(callbacks) == 1

    assert (
        "44:44:33:11:23:45"
        in connectable_scanner.discovered_devices_and_advertisement_data
    )

    not_connectable_scanner = FakeScanner(
        "not_connectable",
        "not_connectable",
        connector,
        False,
    )
    unsetup_not_connectable_scanner = not_connectable_scanner.async_setup()
    cancel_not_connectable_scanner = _get_manager().async_register_scanner(
        not_connectable_scanner
    )
    not_connectable_scanner.inject_advertisement(
        switchbot_device_non_connectable, switchbot_device_adv
    )
    assert async_scanner_count(hass, connectable=True) == 1
    assert async_scanner_count(hass, connectable=False) == 2

    assert (
        "44:44:33:11:23:45"
        in not_connectable_scanner.discovered_devices_and_advertisement_data
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
        switchbot_device_connectable.address,
        connectable=True,
    )

    assert async_scanner_count(hass, connectable=True) == 1
    cancel_connectable_scanner()
    unsetup_connectable_scanner()
    assert async_scanner_count(hass, connectable=True) == 0
    assert async_scanner_count(hass, connectable=False) == 1

    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
    )
    await hass.async_block_till_done()
    assert "44:44:33:11:23:45" in unavailable_callbacks
    cancel_unavailable()

    connectable_scanner_2 = FakeScanner(
        "connectable",
        "connectable",
        connector,
        True,
    )
    unsetup_connectable_scanner_2 = connectable_scanner_2.async_setup()
    cancel_connectable_scanner_2 = _get_manager().async_register_scanner(
        connectable_scanner
    )
    connectable_scanner_2.inject_advertisement(
        switchbot_device_connectable, switchbot_device_adv
    )
    assert (
        "44:44:33:11:23:45"
        in connectable_scanner_2.discovered_devices_and_advertisement_data
    )

    # We should get another callback to make the device available again
    assert len(callbacks) == 2

    cancel()
    cancel_connectable_scanner_2()
    unsetup_connectable_scanner_2()
    cancel_not_connectable_scanner()
    unsetup_not_connectable_scanner()