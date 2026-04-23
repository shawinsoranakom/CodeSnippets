async def test_flow_reauth(hass: HomeAssistant) -> None:
    """Test a reauth flow."""
    entry = create_entry(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    new_conf = {CONF_API_TOKEN: "1234567890123"}
    with patch_discord_login() as mock:
        mock.side_effect = nextcord.LoginFailure
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=new_conf,
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}

    with mocked_discord_info(), patch_discord_login():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=new_conf,
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == CONF_DATA | new_conf