async def test_load_detect_invalid_token(
    hass: HomeAssistant,
    mock_config_entry_v2: MockConfigEntry,
    mock_homewizardenergy_v2: MagicMock,
) -> None:
    """Test setup detects invalid token."""
    mock_homewizardenergy_v2.combined.side_effect = UnauthorizedError()
    mock_config_entry_v2.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_v2.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry_v2.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm_update_token"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == mock_config_entry_v2.entry_id