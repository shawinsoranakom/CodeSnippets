async def test_rpc_smoke_mute_alarm_button(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC smoke mute alarm button."""
    entity_id = f"{BUTTON_DOMAIN}.test_name_mute_alarm"
    monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
    monkeypatch.setattr(mock_rpc_device, "config", {"smoke:0": {"id": 0, "name": None}})
    monkeypatch.setattr(mock_rpc_device, "connected", False)
    await init_integration(hass, 2, sleep_period=1000, model=MODEL_PLUS_SMOKE)

    # Sensor should be created when device is online
    assert hass.states.get(entity_id) is None

    # Make device online
    mock_rpc_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNAVAILABLE

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "smoke:0", "alarm", True)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNKNOWN

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_rpc_device.mock_update()
    mock_rpc_device.smoke_mute_alarm.assert_called_once_with(0)

    monkeypatch.setattr(mock_rpc_device, "initialized", False)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNAVAILABLE