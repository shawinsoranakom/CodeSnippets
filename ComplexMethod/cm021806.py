async def test_reauth_triggered_on_auth_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_trmnl_client: AsyncMock,
) -> None:
    """Test that a reauth flow is triggered when an auth error occurs."""
    mock_trmnl_client.get_devices.side_effect = TRMNLAuthenticationError

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "user"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == mock_config_entry.entry_id