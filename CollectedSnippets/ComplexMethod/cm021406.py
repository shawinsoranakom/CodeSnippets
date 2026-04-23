async def test_control_device_fail(hass: HomeAssistant, mock_bridge, mock_api) -> None:
    """Test control device fail."""
    await init_integration(hass)
    assert mock_bridge

    # Test initial hvac mode - cool
    state = hass.states.get(ENTITY_ID)
    assert state.state == HVACMode.COOL

    # Test exception during set hvac mode
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.control_breeze_device",
        side_effect=RuntimeError("fake error"),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE,
                {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
                blocking=True,
            )

        assert mock_api.call_count == 2
        mock_control_device.assert_called_once_with(
            ANY, state=DeviceState.ON, mode=ThermostatMode.HEAT
        )
        state = hass.states.get(ENTITY_ID)
        assert state.state == STATE_UNAVAILABLE

    # Make device available again
    mock_bridge.mock_callbacks([DEVICE])
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state.state == HVACMode.COOL

    # Test error response during turn on
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.control_breeze_device",
        return_value=SwitcherBaseResponse(None),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE,
                {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
                blocking=True,
            )

        assert mock_api.call_count == 4
        mock_control_device.assert_called_once_with(
            ANY, state=DeviceState.ON, mode=ThermostatMode.HEAT
        )
        state = hass.states.get(ENTITY_ID)
        assert state.state == STATE_UNAVAILABLE