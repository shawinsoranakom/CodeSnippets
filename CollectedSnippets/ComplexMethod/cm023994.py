async def test_async_ble_device_from_address(
    hass: HomeAssistant, mock_bleak_scanner_start: MagicMock
) -> None:
    """Test the async_ble_device_from_address api."""
    set_manager(None)
    mock_bt = []
    with (
        patch(
            "homeassistant.components.bluetooth.async_get_bluetooth",
            return_value=mock_bt,
        ),
        patch(
            "bleak.BleakScanner.discovered_devices_and_advertisement_data",  # Must patch before we setup
            {
                "44:44:33:11:23:45": (
                    MagicMock(address="44:44:33:11:23:45"),
                    MagicMock(),
                )
            },
        ),
    ):
        with pytest.raises(RuntimeError, match="BluetoothManager has not been set"):
            assert not bluetooth.async_discovered_service_info(hass)
        with pytest.raises(RuntimeError, match="BluetoothManager has not been set"):
            assert not bluetooth.async_address_present(hass, "44:44:22:22:11:22")
        with pytest.raises(RuntimeError, match="BluetoothManager has not been set"):
            assert (
                bluetooth.async_ble_device_from_address(hass, "44:44:33:11:23:45")
                is None
            )

        await async_setup_with_default_adapter(hass)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        assert len(mock_bleak_scanner_start.mock_calls) == 1

        assert not bluetooth.async_discovered_service_info(hass)

        switchbot_device = generate_ble_device("44:44:33:11:23:45", "wohand")
        switchbot_adv = generate_advertisement_data(
            local_name="wohand", service_uuids=[]
        )
        inject_advertisement(hass, switchbot_device, switchbot_adv)
        await hass.async_block_till_done()

        assert (
            bluetooth.async_ble_device_from_address(hass, "44:44:33:11:23:45")
            is switchbot_device
        )

        assert (
            bluetooth.async_ble_device_from_address(hass, "00:66:33:22:11:22") is None
        )