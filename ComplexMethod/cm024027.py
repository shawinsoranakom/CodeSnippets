async def test_basic_usage(hass: HomeAssistant) -> None:
    """Test basic usage of the PassiveBluetoothDataUpdateCoordinator."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    coordinator = MyCoordinator(
        hass, _LOGGER, "aa:bb:cc:dd:ee:ff", BluetoothScanningMode.ACTIVE
    )
    assert coordinator.available is False  # no data yet

    mock_listener = MagicMock()
    unregister_listener = coordinator.async_add_listener(mock_listener)

    cancel = coordinator.async_start()

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)

    assert len(mock_listener.mock_calls) == 1
    assert coordinator.data == {"rssi": GENERIC_BLUETOOTH_SERVICE_INFO.rssi}
    assert coordinator.available is True

    unregister_listener()
    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)

    assert len(mock_listener.mock_calls) == 1
    assert coordinator.data == {"rssi": GENERIC_BLUETOOTH_SERVICE_INFO.rssi}
    assert coordinator.available is True
    cancel()