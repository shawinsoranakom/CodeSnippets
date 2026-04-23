async def test_test_switch_adapters_when_out_of_slots(
    hass: HomeAssistant,
    install_bleak_catcher,
    mock_platform_client,
) -> None:
    """Ensure we try another scanner when one runs out of slots."""
    manager = _get_manager()
    hci0_device_advs, cancel_hci0, cancel_hci1 = _generate_scanners_with_fake_devices(
        hass
    )
    # hci0 has 2 slots, hci1 has 1 slot
    with (
        patch.object(manager.slot_manager, "release_slot") as release_slot_mock,
        patch.object(
            manager.slot_manager, "allocate_slot", return_value=True
        ) as allocate_slot_mock,
    ):
        ble_device = hci0_device_advs["00:00:00:00:00:01"][0]
        client = bleak.BleakClient(ble_device)
        await client.connect()
        assert client.is_connected is True
        assert allocate_slot_mock.call_count == 1
        assert release_slot_mock.call_count == 0

    # All adapters are out of slots
    with (
        patch.object(manager.slot_manager, "release_slot") as release_slot_mock,
        patch.object(
            manager.slot_manager, "allocate_slot", return_value=False
        ) as allocate_slot_mock,
    ):
        ble_device = hci0_device_advs["00:00:00:00:00:02"][0]
        client = bleak.BleakClient(ble_device)
        with pytest.raises(bleak.exc.BleakError):
            await client.connect()
        assert allocate_slot_mock.call_count == 2
        assert release_slot_mock.call_count == 0

    # When hci0 runs out of slots, we should try hci1
    def _allocate_slot_mock(ble_device: BLEDevice):
        if "hci1" in ble_device.details["path"]:
            return True
        return False

    with (
        patch.object(manager.slot_manager, "release_slot") as release_slot_mock,
        patch.object(
            manager.slot_manager, "allocate_slot", _allocate_slot_mock
        ) as allocate_slot_mock,
    ):
        ble_device = hci0_device_advs["00:00:00:00:00:03"][0]
        client = bleak.BleakClient(ble_device)
        await client.connect()
        assert client.is_connected is True
        assert release_slot_mock.call_count == 0

    cancel_hci0()
    cancel_hci1()