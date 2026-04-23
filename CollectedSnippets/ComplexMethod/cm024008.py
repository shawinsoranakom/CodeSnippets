async def test_polling_rejecting_the_first_time(hass: HomeAssistant) -> None:
    """Test need_poll rejects the first time ActiveBluetoothDataUpdateCoordinator."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    attempt = 0

    def _needs_poll(
        service_info: BluetoothServiceInfoBleak, seconds_since_last_poll: float | None
    ) -> bool:
        nonlocal attempt
        attempt += 1
        return attempt != 1

    async def _poll_method(service_info: BluetoothServiceInfoBleak) -> dict[str, Any]:
        return {"fake": "data"}

    coordinator = MyCoordinator(
        hass=hass,
        logger=_LOGGER,
        address="aa:bb:cc:dd:ee:ff",
        mode=BluetoothScanningMode.ACTIVE,
        needs_poll_method=_needs_poll,
        poll_method=_poll_method,
    )
    assert coordinator.available is False  # no data yet

    mock_listener = MagicMock()
    unregister_listener = coordinator.async_add_listener(mock_listener)

    cancel = coordinator.async_start()

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.passive_data == {"rssi": GENERIC_BLUETOOTH_SERVICE_INFO.rssi}
    # First poll is rejected, so no data yet
    assert coordinator.data is None

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.passive_data == {"rssi": GENERIC_BLUETOOTH_SERVICE_INFO.rssi}
    # Data is the same so no poll check
    assert coordinator.data is None

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO_2)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.passive_data == {"rssi": GENERIC_BLUETOOTH_SERVICE_INFO_2.rssi}
    # Data is different so poll is done
    assert coordinator.data == {"fake": "data"}

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.passive_data == {"rssi": GENERIC_BLUETOOTH_SERVICE_INFO.rssi}
    # Data is different again so poll is done
    assert coordinator.data == {"fake": "data"}

    cancel()
    unregister_listener()