async def test_auth_error(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_accuweather_client: AsyncMock,
) -> None:
    """Test authentication error when polling data."""
    mock_accuweather_client.async_get_current_conditions.side_effect = (
        InvalidApiKeyError("Invalid API Key")
    )

    mock_config_entry = await init_integration(hass)

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == mock_config_entry.entry_id