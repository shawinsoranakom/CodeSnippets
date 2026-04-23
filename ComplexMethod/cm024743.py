async def test_reauth_flow(hass: HomeAssistant, cfupdate_flow: MagicMock) -> None:
    """Test the reauthentication configuration flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_TOKEN: "other_token"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert entry.data[CONF_API_TOKEN] == "other_token"
    assert entry.data[CONF_ZONE] == ENTRY_CONFIG[CONF_ZONE]
    assert entry.data[CONF_RECORDS] == ENTRY_CONFIG[CONF_RECORDS]

    assert len(mock_setup_entry.mock_calls) == 1