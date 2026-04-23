async def test_step_reauth(
    hass: HomeAssistant, mock_ttnclient, mock_config_entry: MockConfigEntry
) -> None:
    """Test that the reauth step works."""

    await init_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    new_api_key = "1234"
    new_user_input = dict(USER_DATA)
    new_user_input[CONF_API_KEY] = new_api_key

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=new_user_input
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert len(hass.config_entries.async_entries()) == 1
    assert hass.config_entries.async_entries()[0].data[CONF_API_KEY] == new_api_key