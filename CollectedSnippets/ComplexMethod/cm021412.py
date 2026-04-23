async def test_switch_control_fail(
    hass: HomeAssistant,
    mock_bridge,
    mock_api,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test switch control fail."""
    await init_integration(hass)
    assert mock_bridge

    device = DUMMY_PLUG_DEVICE
    entity_id = f"{SWITCH_DOMAIN}.{slugify(device.name)}"

    # Test initial state - off
    monkeypatch.setattr(device, "device_state", DeviceState.OFF)
    mock_bridge.mock_callbacks([DUMMY_PLUG_DEVICE])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Test exception during turn on
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.control_device",
        side_effect=RuntimeError("fake error"),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                SWITCH_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )

        assert mock_api.call_count == 2
        mock_control_device.assert_called_once_with(Command.ON)
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNAVAILABLE

    # Make device available again
    mock_bridge.mock_callbacks([DUMMY_PLUG_DEVICE])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Test error response during turn on
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.control_device",
        return_value=SwitcherBaseResponse(None),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                SWITCH_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )

        assert mock_api.call_count == 4
        mock_control_device.assert_called_once_with(Command.ON)
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNAVAILABLE