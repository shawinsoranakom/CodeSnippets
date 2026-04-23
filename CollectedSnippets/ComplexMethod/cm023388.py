async def test_flow_reauth_errors(
    hass: HomeAssistant,
    mock_psnawpapi: MagicMock,
    config_entry: MockConfigEntry,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test reauth flow errors."""

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    mock_psnawpapi.user.side_effect = raise_error
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: "NEW_NPSSO_TOKEN"},
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    mock_psnawpapi.user.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NPSSO: "NEW_NPSSO_TOKEN"},
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert config_entry.data[CONF_NPSSO] == "NEW_NPSSO_TOKEN"

    assert len(hass.config_entries.async_entries()) == 1