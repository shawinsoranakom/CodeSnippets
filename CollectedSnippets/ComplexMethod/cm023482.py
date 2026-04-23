async def test_reconfigure_error_then_fix(
    hass: HomeAssistant,
    toloclient: Mock,
    coordinator_toloclient: Mock,
    config_entry: MockConfigEntry,
) -> None:
    """Test a reconfigure flow which first fails and then recovers."""
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "user"

    toloclient().get_status.side_effect = ToloCommunicationError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.5"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "cannot_connect"

    toloclient().get_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.4"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data[CONF_HOST] == "127.0.0.4"