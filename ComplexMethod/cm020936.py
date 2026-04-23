async def test_config_auth_failed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_nextdns: AsyncMock,
) -> None:
    """Test for setup failure if the auth fails."""
    mock_nextdns.create.side_effect = InvalidApiKeyError

    await init_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == mock_config_entry.entry_id