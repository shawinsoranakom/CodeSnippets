async def test_coordinator_update_auth_failed(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_psnawpapi: MagicMock,
) -> None:
    """Test coordinator update auth failed setup error."""

    mock_psnawpapi.user.return_value.get_presence.side_effect = (
        PSNAWPAuthenticationError("error msg")
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow.get("step_id") == "reauth_confirm"
    assert flow.get("handler") == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == config_entry.entry_id