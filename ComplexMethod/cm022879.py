async def test_full_flow_reauth_token_other(
    hass: HomeAssistant,
    mock_proxmox_client: MagicMock,
    mock_setup_entry: MagicMock,
    mock_config_entry_token_other: MockConfigEntry,
) -> None:
    """Test the full flow of the config flow."""
    mock_config_entry_token_other.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await mock_config_entry_token_other.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # There is no user input
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_REALM: "test_realm",
            CONF_TOKEN_ID: "test_token_id",
            CONF_TOKEN_SECRET: "new_token_secret",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry_token_other.data[CONF_TOKEN_SECRET] == "new_token_secret"
    assert len(mock_setup_entry.mock_calls) == 1