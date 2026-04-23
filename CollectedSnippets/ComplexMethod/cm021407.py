async def test_control_device_fail(
    hass: HomeAssistant, mock_bridge, mock_api, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test control device fail."""
    await init_integration(hass)
    assert mock_bridge

    assert hass.states.get(ASSUME_ON_EID) is not None

    # Test exception during set hvac mode
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.control_breeze_device",
        side_effect=RuntimeError("fake error"),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: ASSUME_ON_EID},
                blocking=True,
            )

        assert mock_api.call_count == 2
        mock_control_device.assert_called_once_with(
            ANY, state=DeviceState.ON, update_state=True
        )

        state = hass.states.get(ASSUME_ON_EID)
        assert state.state == STATE_UNAVAILABLE

    # Make device available again
    mock_bridge.mock_callbacks([DEVICE])
    await hass.async_block_till_done()

    assert hass.states.get(ASSUME_ON_EID) is not None

    # Test error response during turn on
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.control_breeze_device",
        return_value=SwitcherBaseResponse(None),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: ASSUME_ON_EID},
                blocking=True,
            )

        assert mock_api.call_count == 4
        mock_control_device.assert_called_once_with(
            ANY, state=DeviceState.ON, update_state=True
        )

        state = hass.states.get(ASSUME_ON_EID)
        assert state.state == STATE_UNAVAILABLE