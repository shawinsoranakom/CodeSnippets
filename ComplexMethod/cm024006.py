async def test_bleak_error_during_polling(hass: HomeAssistant) -> None:
    """Test bleak error during polling ActiveBluetoothDataUpdateCoordinator."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    poll_count = 0

    def _needs_poll(
        service_info: BluetoothServiceInfoBleak, seconds_since_last_poll: float | None
    ) -> bool:
        return True

    async def _poll_method(service_info: BluetoothServiceInfoBleak) -> dict[str, Any]:
        nonlocal poll_count
        poll_count += 1
        if poll_count == 1:
            raise BleakError("fake bleak error")
        return {"fake": "data"}

    coordinator = MyCoordinator(
        hass=hass,
        logger=_LOGGER,
        address="aa:bb:cc:dd:ee:ff",
        mode=BluetoothScanningMode.ACTIVE,
        needs_poll_method=_needs_poll,
        poll_method=_poll_method,
        poll_debouncer=Debouncer(hass, _LOGGER, cooldown=0, immediate=True),
    )
    assert coordinator.available is False  # no data yet

    mock_listener = MagicMock()
    unregister_listener = coordinator.async_add_listener(mock_listener)

    cancel = coordinator.async_start()

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.passive_data == {"rssi": GENERIC_BLUETOOTH_SERVICE_INFO.rssi}
    assert coordinator.data is None
    assert coordinator.last_poll_successful is False

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO_2)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.passive_data == {"rssi": GENERIC_BLUETOOTH_SERVICE_INFO_2.rssi}
    assert coordinator.data == {"fake": "data"}
    assert coordinator.last_poll_successful is True

    cancel()
    unregister_listener()