async def test_light_control_fail(
    hass: HomeAssistant,
    mock_bridge,
    mock_api,
    monkeypatch: pytest.MonkeyPatch,
    device,
    entity_id: str,
    light_id: int,
    device_state: list[DeviceState],
) -> None:
    """Test light control fail."""
    await init_integration(hass, USERNAME, TOKEN)
    assert mock_bridge

    # Test initial state - light off
    monkeypatch.setattr(device, "light", device_state)
    mock_bridge.mock_callbacks([device])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Test exception during turn on
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_light",
        side_effect=RuntimeError("fake error"),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )

        assert mock_api.call_count == 2
        mock_control_device.assert_called_once_with(DeviceState.ON, light_id)
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNAVAILABLE

    # Make device available again
    mock_bridge.mock_callbacks([device])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Test error response during turn on
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_light",
        return_value=SwitcherBaseResponse(None),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )

        assert mock_api.call_count == 4
        mock_control_device.assert_called_once_with(DeviceState.ON, light_id)
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNAVAILABLE