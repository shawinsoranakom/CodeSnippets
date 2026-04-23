async def test_no_polling_after_stop_event(hass: HomeAssistant) -> None:
    """Test we do not poll after the stop event."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    needs_poll_calls = 0

    def _needs_poll(
        service_info: BluetoothServiceInfoBleak, seconds_since_last_poll: float | None
    ) -> bool:
        nonlocal needs_poll_calls
        needs_poll_calls += 1
        return True

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
    assert needs_poll_calls == 0

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.passive_data == {"rssi": GENERIC_BLUETOOTH_SERVICE_INFO.rssi}
    assert coordinator.data == {"fake": "data"}

    assert needs_poll_calls == 1

    hass.set_state(CoreState.stopping)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert needs_poll_calls == 1

    # Should not generate a poll now
    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO_2)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert needs_poll_calls == 1

    cancel()
    unregister_listener()