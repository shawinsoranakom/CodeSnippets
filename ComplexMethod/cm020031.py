async def test_flow_reauth(hass: HomeAssistant) -> None:
    """Test reauth step."""
    entry = create_entry(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    with patch_interface():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        new_conf = CONF_DATA | {CONF_API_KEY: "1234567890"}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=new_conf,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.data == new_conf