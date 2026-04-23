async def test_reauth_errors(hass: HomeAssistant, client, side_effect, error) -> None:
    """Test reauthorization errors."""
    entry = await setup_webostv(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    client.connect.side_effect = side_effect()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"