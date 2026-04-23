async def test_initialization(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    mock_config_entry: MockConfigEntry,
    mock_mozart_client: AsyncMock,
) -> None:
    """Test the integration is initialized properly in _initialize, async_added_to_hass and __init__."""
    caplog.set_level(logging.DEBUG)

    # Setup entity
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await mock_websocket_connection(hass, mock_mozart_client)

    # Ensure that the logger has been called with the debug message
    assert "Connected to: Beosound Balance 11111111 running SW 1.0.0" in caplog.text

    # Check state (The initial state in this test does not contain all that much.
    # States are tested using simulated WebSocket events.)
    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert states.attributes[ATTR_INPUT_SOURCE_LIST] == TEST_SOURCES
    assert states.attributes[ATTR_MEDIA_POSITION_UPDATED_AT]
    assert states.attributes[ATTR_SOUND_MODE_LIST] == TEST_SOUND_MODES

    # Check API calls
    mock_mozart_client.get_softwareupdate_status.assert_called_once()
    mock_mozart_client.get_available_sources.assert_called_once()
    mock_mozart_client.get_remote_menu.assert_called_once()
    mock_mozart_client.get_listening_mode_set.assert_called_once()
    mock_mozart_client.get_active_listening_mode.assert_called_once()
    mock_mozart_client.get_beolink_self.assert_called_once()
    assert mock_mozart_client.get_beolink_peers.call_count == 2
    assert mock_mozart_client.get_beolink_listeners.call_count == 2