async def test_register_callback_survives_reload(
    hass: HomeAssistant, mock_bleak_scanner_start: MagicMock
) -> None:
    """Test registering a callback by address survives bluetooth being reloaded."""
    mock_bt = []
    callbacks = []

    def _fake_subscriber(
        service_info: BluetoothServiceInfo, change: BluetoothChange
    ) -> None:
        """Fake subscriber for the BleakScanner."""
        callbacks.append((service_info, change))

    with patch(
        "homeassistant.components.bluetooth.async_get_bluetooth", return_value=mock_bt
    ):
        await async_setup_with_default_adapter(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    cancel = bluetooth.async_register_callback(
        hass,
        _fake_subscriber,
        {"address": "44:44:33:11:23:45"},
        BluetoothScanningMode.ACTIVE,
    )

    assert len(mock_bleak_scanner_start.mock_calls) == 1

    switchbot_device = generate_ble_device("44:44:33:11:23:45", "wohand")
    switchbot_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=["zba20d00-224d-11e6-9fb8-0002a5d5c51b"],
        manufacturer_data={89: b"\xd8.\xad\xcd\r\x85"},
        service_data={"00000d00-0000-1000-8000-00805f9b34fb": b"H\x10c"},
    )
    switchbot_adv_2 = generate_advertisement_data(
        local_name="wohand",
        service_uuids=["zba20d00-224d-11e6-9fb8-0002a5d5c51b"],
        manufacturer_data={89: b"\xd8.\xad\xcd\r\x84"},
        service_data={"00000d00-0000-1000-8000-00805f9b34fb": b"H\x10c"},
    )
    inject_advertisement(hass, switchbot_device, switchbot_adv)
    assert len(callbacks) == 1
    service_info: BluetoothServiceInfo = callbacks[0][0]
    assert service_info.name == "wohand"
    assert service_info.manufacturer == "Nordic Semiconductor ASA"
    assert service_info.manufacturer_id == 89

    entry = hass.config_entries.async_entries(bluetooth.DOMAIN)[0]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    inject_advertisement(hass, switchbot_device, switchbot_adv_2)
    assert len(callbacks) == 2
    service_info: BluetoothServiceInfo = callbacks[1][0]
    assert service_info.name == "wohand"
    assert service_info.manufacturer == "Nordic Semiconductor ASA"
    assert service_info.manufacturer_id == 89
    cancel()