async def test_no_polling_after_stop_event(hass: HomeAssistant) -> None:
    """Test we do not poll after the stop event."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    needs_poll_calls = 0

    def _update_method(service_info: BluetoothServiceInfoBleak):
        return {"testdata": 0}

    def _poll_needed(*args, **kwargs):
        nonlocal needs_poll_calls
        needs_poll_calls += 1
        return True

    async def _poll(*args, **kwargs):
        return {"testdata": 1}

    coordinator = ActiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address="aa:bb:cc:dd:ee:ff",
        mode=BluetoothScanningMode.ACTIVE,
        update_method=_update_method,
        needs_poll_method=_poll_needed,
        poll_method=_poll,
    )
    assert coordinator.available is False  # no data yet

    processor = MagicMock()
    coordinator.async_register_processor(processor)
    async_handle_update = processor.async_handle_update

    cancel = coordinator.async_start()

    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert needs_poll_calls == 1

    assert coordinator.available is True

    # async_handle_update should have been called twice
    # The first time, it was passed the data from parsing the advertisement
    # The second time, it was passed the data from polling
    assert len(async_handle_update.mock_calls) == 2
    assert async_handle_update.mock_calls[0] == call({"testdata": 0}, False)
    assert async_handle_update.mock_calls[1] == call({"testdata": 1})

    hass.set_state(CoreState.stopping)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert needs_poll_calls == 1

    # Should not generate a poll now that CoreState is stopping
    inject_bluetooth_service_info(hass, GENERIC_BLUETOOTH_SERVICE_INFO_2)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert needs_poll_calls == 1

    cancel()