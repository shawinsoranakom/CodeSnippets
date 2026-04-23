async def test_device_with_ten_minute_advertising_interval(hass: HomeAssistant) -> None:
    """Test a device with a 10 minute advertising interval."""
    manager = _get_manager()

    bparasite_device = generate_ble_device(
        "44:44:33:11:23:45",
        "bparasite",
        {},
    )
    bparasite_device_adv = generate_advertisement_data(
        local_name="bparasite",
        service_uuids=[],
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner("esp32", "esp32", connector, True)
    unsetup = scanner.async_setup()
    cancel = manager.async_register_scanner(scanner)

    monotonic_now = time.monotonic()
    new_time = monotonic_now
    bparasite_device_went_unavailable = False

    @callback
    def _bparasite_device_unavailable_callback(_address: str) -> None:
        """Barasite device unavailable callback."""
        nonlocal bparasite_device_went_unavailable
        bparasite_device_went_unavailable = True

    advertising_interval = 60 * 10

    bparasite_device_unavailable_cancel = bluetooth.async_track_unavailable(
        hass,
        _bparasite_device_unavailable_callback,
        bparasite_device.address,
        connectable=False,
    )

    with patch_bluetooth_time(new_time):
        scanner.inject_advertisement(bparasite_device, bparasite_device_adv, new_time)

    original_device = scanner.discovered_devices_and_advertisement_data[
        bparasite_device.address
    ][0]
    assert original_device is not bparasite_device

    for _ in range(1, 20):
        new_time += advertising_interval
        with patch_bluetooth_time(new_time):
            scanner.inject_advertisement(
                bparasite_device, bparasite_device_adv, new_time
            )

    # Make sure the BLEDevice object gets updated
    # and not replaced
    assert (
        scanner.discovered_devices_and_advertisement_data[bparasite_device.address][0]
        is original_device
    )

    future_time = new_time
    assert (
        bluetooth.async_address_present(hass, bparasite_device.address, False) is True
    )
    assert bparasite_device_went_unavailable is False
    with patch_bluetooth_time(new_time):
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=future_time))
        await hass.async_block_till_done()

    assert bparasite_device_went_unavailable is False

    missed_advertisement_future_time = (
        future_time + advertising_interval + TRACKER_BUFFERING_WOBBLE_SECONDS + 1
    )

    with patch_bluetooth_time(missed_advertisement_future_time):
        # Fire once for the scanner to expire the device
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
        )
        await hass.async_block_till_done()
        # Fire again for the manager to expire the device
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=missed_advertisement_future_time)
        )
        await hass.async_block_till_done()

    assert (
        bluetooth.async_address_present(hass, bparasite_device.address, False) is False
    )
    assert bparasite_device_went_unavailable is True
    bparasite_device_unavailable_cancel()

    cancel()
    unsetup()