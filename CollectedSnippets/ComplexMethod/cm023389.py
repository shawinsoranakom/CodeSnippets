async def test_flow_reauth_token_error(
    hass: HomeAssistant,
    mock_psnawp_npsso: MagicMock,
    config_entry: MockConfigEntry,
) -> None:
    """Test reauth flow token error."""

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    mock_psnawp_npsso.side_effect = PSNAWPInvalidTokenError("error msg")
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: "NEW_NPSSO_TOKEN"},
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_account"}

    mock_psnawp_npsso.side_effect = lambda token: token
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: "NEW_NPSSO_TOKEN"},
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert config_entry.data[CONF_NPSSO] == "NEW_NPSSO_TOKEN"

    assert len(hass.config_entries.async_entries()) == 1