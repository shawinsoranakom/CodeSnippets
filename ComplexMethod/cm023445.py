async def test_flow_reauth_error_and_recover(
    hass: HomeAssistant,
    mock_bring_client: AsyncMock,
    bring_config_entry: MockConfigEntry,
    raise_error,
    text_error,
) -> None:
    """Test reauth flow."""

    bring_config_entry.add_to_hass(hass)

    result = await bring_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_bring_client.login.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    mock_bring_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "new-email", CONF_PASSWORD: "new-password"},
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert len(hass.config_entries.async_entries()) == 1