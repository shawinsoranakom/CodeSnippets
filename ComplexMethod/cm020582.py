async def test_upnp_failed_re_subscribe_events(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    remote_websocket: Mock,
    dmr_device: Mock,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
) -> None:
    """Test for Upnp event feedback."""
    await setup_samsungtv_entry(hass, MOCK_ENTRY_WS)

    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    assert dmr_device.async_subscribe_services.call_count == 1
    assert dmr_device.async_unsubscribe_services.call_count == 0

    with (
        patch.object(
            remote_websocket, "start_listening", side_effect=WebSocketException("Boom")
        ),
        patch.object(remote_websocket, "is_alive", return_value=False),
    ):
        freezer.tick(timedelta(minutes=5))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert dmr_device.async_subscribe_services.call_count == 1
    assert dmr_device.async_unsubscribe_services.call_count == 1

    with patch.object(dmr_device, "async_subscribe_services", side_effect=error):
        freezer.tick(timedelta(minutes=5))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    assert "Device rejected re-subscription" in caplog.text