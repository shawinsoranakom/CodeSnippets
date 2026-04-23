async def test_cover(
    hass: HomeAssistant,
    mock_bridge,
    mock_api,
    monkeypatch: pytest.MonkeyPatch,
    device,
    entity_id: str,
    cover_id: int,
    position_open: list[int],
    position_close: list[int],
    direction_open: list[ShutterDirection],
    direction_close: list[ShutterDirection],
    direction_stop: list[ShutterDirection],
) -> None:
    """Test cover services."""
    await init_integration(hass, USERNAME, TOKEN)
    assert mock_bridge

    # Test initial state - open
    state = hass.states.get(entity_id)
    assert state.state == CoverState.OPEN

    # Test set position
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_position"
    ) as mock_control_device:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 77},
            blocking=True,
        )

        monkeypatch.setattr(device, "position", position_open)
        mock_bridge.mock_callbacks([device])
        await hass.async_block_till_done()

        assert mock_api.call_count == 2
        mock_control_device.assert_called_once_with(77, cover_id)
        state = hass.states.get(entity_id)
        assert state.state == CoverState.OPEN
        assert state.attributes[ATTR_CURRENT_POSITION] == 77

    # Test open
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_position"
    ) as mock_control_device:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        monkeypatch.setattr(device, "direction", direction_open)
        mock_bridge.mock_callbacks([device])
        await hass.async_block_till_done()

        assert mock_api.call_count == 4
        mock_control_device.assert_called_once_with(100, cover_id)
        state = hass.states.get(entity_id)
        assert state.state == CoverState.OPENING

    # Test close
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.set_position"
    ) as mock_control_device:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        monkeypatch.setattr(device, "direction", direction_close)
        mock_bridge.mock_callbacks([device])
        await hass.async_block_till_done()

        assert mock_api.call_count == 6
        mock_control_device.assert_called_once_with(0, cover_id)
        state = hass.states.get(entity_id)
        assert state.state == CoverState.CLOSING

    # Test stop
    with patch(
        "homeassistant.components.switcher_kis.entity.SwitcherApi.stop_shutter"
    ) as mock_control_device:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        monkeypatch.setattr(device, "direction", direction_stop)
        mock_bridge.mock_callbacks([device])
        await hass.async_block_till_done()

        assert mock_api.call_count == 8
        mock_control_device.assert_called_once_with(cover_id)
        state = hass.states.get(entity_id)
        assert state.state == CoverState.OPEN

    # Test closed on position == 0
    monkeypatch.setattr(device, "position", position_close)
    mock_bridge.mock_callbacks([device])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == CoverState.CLOSED
    assert state.attributes[ATTR_CURRENT_POSITION] == 0