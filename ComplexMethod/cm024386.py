async def test_reauth_successful(hass: HomeAssistant, client) -> None:
    """Test that the reauthorization is successful."""
    entry = await setup_webostv(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert entry.data[CONF_CLIENT_SECRET] == CLIENT_KEY

    client.client_key = "new_key"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_CLIENT_SECRET] == "new_key"