async def test_child_lock_switch(
    hass: HomeAssistant,
    mock_bridge,
    mock_api,
    monkeypatch: pytest.MonkeyPatch,
    device,
    entity_id: str,
    cover_id: int,
    child_lock_state: list[ShutterChildLock],
) -> None:
    """Test the switch."""
    await init_integration(hass, USERNAME, TOKEN)
    assert mock_bridge

    # Test initial state - on
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    # Test state change on --> off
    monkeypatch.setattr(device, "child_lock", child_lock_state)
    mock_bridge.mock_callbacks([device])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Test turning on child lock
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_shutter_child_lock",
    ) as mock_control_device:
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        assert mock_api.call_count == 2
        mock_control_device.assert_called_once_with(ShutterChildLock.ON, cover_id)
        state = hass.states.get(entity_id)
        assert state.state == STATE_ON

    # Test turning off
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_shutter_child_lock"
    ) as mock_control_device:
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        assert mock_api.call_count == 4
        mock_control_device.assert_called_once_with(ShutterChildLock.OFF, cover_id)
        state = hass.states.get(entity_id)
        assert state.state == STATE_OFF