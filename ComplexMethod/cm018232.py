async def test_auth_failed(
    hass: HomeAssistant, ista_config_entry: MockConfigEntry, mock_ista: MagicMock
) -> None:
    """Test coordinator auth failed and reauth flow started."""
    with patch(
        "homeassistant.components.ista_ecotrend.PLATFORMS",
        [],
    ):
        mock_ista.get_consumption_data.side_effect = LoginError
        ista_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(ista_config_entry.entry_id)
        await hass.async_block_till_done()

        assert ista_config_entry.state is ConfigEntryState.SETUP_ERROR

        flows = hass.config_entries.flow.async_progress()
        assert len(flows) == 1

        flow = flows[0]
        assert flow.get("step_id") == "reauth_confirm"
        assert flow.get("handler") == DOMAIN

        assert "context" in flow
        assert flow["context"].get("source") == SOURCE_REAUTH
        assert flow["context"].get("entry_id") == ista_config_entry.entry_id