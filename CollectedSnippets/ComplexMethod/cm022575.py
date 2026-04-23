async def test_reauthentication_trigger_key_read_only(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test reauthentication trigger."""
    mock_config_entry = MockConfigEntry(
        **MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA_KEY_READ_ONLY
    )
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    assert (
        mock_config_entry.reason
        == "Wrong API key type detected, use the 'main' API key"
    )

    assert len(flows) == 1
    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert flow["context"]["source"] == config_entries.SOURCE_REAUTH
    assert flow["context"]["entry_id"] == mock_config_entry.entry_id

    assert (
        "Config entry 'test@test.test' for uptimerobot integration could not authenticate"
        in caplog.text
    )