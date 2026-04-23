async def test_remote_scanner(hass: HomeAssistant, name_2: str | None) -> None:
    """Test the remote scanner base class merges advertisement_data."""
    manager = _get_manager()

    switchbot_device = generate_ble_device(
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
    switchbot_device_2 = generate_ble_device(
        "44:44:33:11:23:45",
        name_2,
        {},
    )
    switchbot_device_adv_2 = generate_advertisement_data(
        local_name=name_2,
        service_uuids=["00000001-0000-1000-8000-00805f9b34fb"],
        service_data={"00000001-0000-1000-8000-00805f9b34fb": b"\n\xff"},
        manufacturer_data={1: b"\x01", 2: b"\x02"},
        rssi=-100,
    )
    switchbot_device_3 = generate_ble_device(
        "44:44:33:11:23:45",
        "wohandlonger",
        {},
    )
    switchbot_device_adv_3 = generate_advertisement_data(
        local_name="wohandlonger",
        service_uuids=["00000001-0000-1000-8000-00805f9b34fb"],
        service_data={"00000001-0000-1000-8000-00805f9b34fb": b"\n\xff"},
        manufacturer_data={1: b"\x01", 2: b"\x02"},
        rssi=-100,
    )

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner("esp32", "esp32", connector, True)
    unsetup = scanner.async_setup()
    cancel = manager.async_register_scanner(scanner)

    scanner.inject_advertisement(switchbot_device, switchbot_device_adv)

    data = scanner.discovered_devices_and_advertisement_data
    discovered_device, discovered_adv_data = data[switchbot_device.address]
    assert discovered_device.address == switchbot_device.address
    assert discovered_device.name == switchbot_device.name
    assert (
        discovered_adv_data.manufacturer_data == switchbot_device_adv.manufacturer_data
    )
    assert discovered_adv_data.service_data == switchbot_device_adv.service_data
    assert discovered_adv_data.service_uuids == switchbot_device_adv.service_uuids
    scanner.inject_advertisement(switchbot_device_2, switchbot_device_adv_2)

    data = scanner.discovered_devices_and_advertisement_data
    discovered_device, discovered_adv_data = data[switchbot_device.address]
    assert discovered_device.address == switchbot_device.address
    assert discovered_device.name == switchbot_device.name
    assert discovered_adv_data.manufacturer_data == {1: b"\x01", 2: b"\x02"}
    assert discovered_adv_data.service_data == {
        "050a021a-0000-1000-8000-00805f9b34fb": b"\n\xff",
        "00000001-0000-1000-8000-00805f9b34fb": b"\n\xff",
    }
    assert set(discovered_adv_data.service_uuids) == {
        "050a021a-0000-1000-8000-00805f9b34fb",
        "00000001-0000-1000-8000-00805f9b34fb",
    }

    # The longer name should be used
    scanner.inject_advertisement(switchbot_device_3, switchbot_device_adv_3)
    assert discovered_device.name == switchbot_device_3.name

    # Inject the shorter name / None again to make
    # sure we always keep the longer name
    scanner.inject_advertisement(switchbot_device_2, switchbot_device_adv_2)
    assert discovered_device.name == switchbot_device_3.name

    cancel()
    unsetup()