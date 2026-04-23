async def test_invalid_auth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_lamarzocco: MagicMock,
) -> None:
    """Test auth error during setup."""
    mock_lamarzocco.websocket.connected = False
    mock_lamarzocco.get_dashboard.side_effect = AuthFail("")
    await async_init_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    assert len(mock_lamarzocco.get_dashboard.mock_calls) == 1

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == mock_config_entry.entry_id