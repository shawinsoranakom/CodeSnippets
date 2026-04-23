async def test_cover_control_fail(
    hass: HomeAssistant,
    mock_bridge,
    mock_api,
    device,
    entity_id: str,
    cover_id: int,
) -> None:
    """Test cover control fail."""
    await init_integration(hass, USERNAME, TOKEN)
    assert mock_bridge

    # Test initial state - open
    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPEN

    # Test exception during set position
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_position",
        side_effect=RuntimeError("fake error"),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_SET_COVER_POSITION,
                {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 44},
                blocking=True,
            )

        assert mock_api.call_count == 2
        mock_control_device.assert_called_once_with(44, cover_id)
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNAVAILABLE

    # Make device available again
    mock_bridge.mock_callbacks([device])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPEN

    # Test error response during set position
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_position",
        return_value=SwitcherBaseResponse(None),
    ) as mock_control_device:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_SET_COVER_POSITION,
                {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 27},
                blocking=True,
            )

        assert mock_api.call_count == 4
        mock_control_device.assert_called_once_with(27, cover_id)
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNAVAILABLE