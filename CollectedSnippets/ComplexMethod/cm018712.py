async def test_attributes_group_is_none(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_create_server: AsyncMock,
    mock_client_1: AsyncMock,
) -> None:
    """Test exceptions are not thrown when a client has no group."""
    # Force nonexistent group
    mock_client_1.group = None

    # Setup and verify the integration is loaded
    with patch("secrets.token_hex", return_value="mock_token"):
        await setup_integration(hass, mock_config_entry)
        assert mock_config_entry.state is ConfigEntryState.LOADED

    state = hass.states.get("media_player.test_client_1_snapcast_client")

    # Assert accessing state and attributes doesn't throw
    assert state.state == MediaPlayerState.IDLE

    assert state.attributes["group_members"] is None
    assert "source" not in state.attributes
    assert "source_list" not in state.attributes
    assert "metadata" not in state.attributes
    assert "media_position" not in state.attributes