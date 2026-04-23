async def test_rpc_cover_position_update(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC update_position while the cover is moving."""
    entity_id = "cover.test_name_test_cover_0"
    await init_integration(hass, 2)

    # Set initial state to closing, position 50 set by update_cover_status mock
    mutate_rpc_device_status(
        monkeypatch, mock_rpc_device, "cover:0", "state", "closing"
    )
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == CoverState.CLOSING
    assert state.attributes[ATTR_CURRENT_POSITION] == 50

    # Simulate position updates during closing
    for position in range(40, -1, -10):
        mock_rpc_device.update_cover_status.reset_mock()
        await mock_polling_rpc_update(hass, freezer, RPC_COVER_UPDATE_TIME_SEC)

        mock_rpc_device.update_cover_status.assert_called_once_with(0)
        assert (state := hass.states.get(entity_id))
        assert state.attributes[ATTR_CURRENT_POSITION] == position
        assert state.state == CoverState.CLOSING

    # Simulate cover reaching final position
    mock_rpc_device.update_cover_status.reset_mock()
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cover:0", "state", "closed")
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_CURRENT_POSITION] == 0
    assert state.state == CoverState.CLOSED

    # Ensure update_position does not call update_cover_status when the cover is not moving
    await mock_polling_rpc_update(hass, freezer, RPC_COVER_UPDATE_TIME_SEC)
    mock_rpc_device.update_cover_status.assert_not_called()