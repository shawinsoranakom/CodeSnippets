async def test_wrapped_instance_with_filter(
    hass: HomeAssistant, mock_bleak_scanner_start: MagicMock
) -> None:
    """Test consumers can use the wrapped instance with a filter as if it was normal BleakScanner."""
    with patch(
        "homeassistant.components.bluetooth.async_get_bluetooth", return_value=[]
    ):
        await async_setup_with_default_adapter(hass)

    with patch.object(hass.config_entries.flow, "async_init"):
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        detected = []

        def _device_detected(
            device: BLEDevice, advertisement_data: AdvertisementData
        ) -> None:
            """Handle a detected device."""
            detected.append((device, advertisement_data))

        switchbot_device = generate_ble_device("44:44:33:11:23:45", "wohand")
        switchbot_adv = generate_advertisement_data(
            local_name="wohand",
            service_uuids=["cba20d00-224d-11e6-9fb8-0002a5d5c51b"],
            manufacturer_data={89: b"\xd8.\xad\xcd\r\x85"},
            service_data={"00000d00-0000-1000-8000-00805f9b34fb": b"H\x10c"},
        )
        switchbot_adv_2 = generate_advertisement_data(
            local_name="wohand",
            service_uuids=["cba20d00-224d-11e6-9fb8-0002a5d5c51b"],
            manufacturer_data={89: b"\xd8.\xad\xcd\r\x84"},
            service_data={"00000d00-0000-1000-8000-00805f9b34fb": b"H\x10c"},
        )
        empty_device = generate_ble_device("11:22:33:44:55:66", "empty")
        empty_adv = generate_advertisement_data(local_name="empty")

        assert _get_manager() is not None
        scanner = HaBleakScannerWrapper(
            filters={"UUIDs": ["cba20d00-224d-11e6-9fb8-0002a5d5c51b"]}
        )
        scanner.register_detection_callback(_device_detected)

        inject_advertisement(hass, switchbot_device, switchbot_adv_2)
        await hass.async_block_till_done()

        discovered = await scanner.discover(timeout=0)
        assert len(discovered) == 1
        assert discovered == [switchbot_device]
        assert len(detected) == 1

        scanner.register_detection_callback(_device_detected)
        # We should get a reply from the history when we register again
        assert len(detected) == 2
        scanner.register_detection_callback(_device_detected)
        # We should get a reply from the history when we register again
        assert len(detected) == 3

        with patch_discovered_devices([]):
            discovered = await scanner.discover(timeout=0)
            assert len(discovered) == 0
            assert discovered == []

        inject_advertisement(hass, switchbot_device, switchbot_adv)
        assert len(detected) == 4

        # The filter we created in the wrapped scanner with should be respected
        # and we should not get another callback
        inject_advertisement(hass, empty_device, empty_adv)
        assert len(detected) == 4