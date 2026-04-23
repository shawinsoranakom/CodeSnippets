async def test_register_callbacks_raises_exception(
    hass: HomeAssistant,
    mock_bleak_scanner_start: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test registering a callback that raises ValueError."""
    mock_bt = []
    callbacks = []

    def _fake_subscriber(
        service_info: BluetoothServiceInfo,
        change: BluetoothChange,
    ) -> None:
        """Fake subscriber for the BleakScanner."""
        callbacks.append((service_info, change))
        raise ValueError

    with (
        patch(
            "homeassistant.components.bluetooth.async_get_bluetooth",
            return_value=mock_bt,
        ),
        patch.object(hass.config_entries.flow, "async_init"),
    ):
        await async_setup_with_default_adapter(hass)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        cancel = bluetooth.async_register_callback(
            hass,
            _fake_subscriber,
            {SERVICE_UUID: "cba20d00-224d-11e6-9fb8-0002a5d5c51b"},
            BluetoothScanningMode.ACTIVE,
        )

        assert len(mock_bleak_scanner_start.mock_calls) == 1

        switchbot_device = generate_ble_device("44:44:33:11:23:45", "wohand")
        switchbot_adv = generate_advertisement_data(
            local_name="wohand",
            service_uuids=["cba20d00-224d-11e6-9fb8-0002a5d5c51b"],
            manufacturer_data={89: b"\xd8.\xad\xcd\r\x85"},
            service_data={"00000d00-0000-1000-8000-00805f9b34fb": b"H\x10c"},
        )

        inject_advertisement(hass, switchbot_device, switchbot_adv)

        cancel()

        inject_advertisement(hass, switchbot_device, switchbot_adv)
        await hass.async_block_till_done()

    assert len(callbacks) == 1

    service_info: BluetoothServiceInfo = callbacks[0][0]
    assert service_info.name == "wohand"
    assert service_info.source == SOURCE_LOCAL
    assert service_info.manufacturer == "Nordic Semiconductor ASA"
    assert service_info.manufacturer_id == 89

    assert "ValueError" in caplog.text