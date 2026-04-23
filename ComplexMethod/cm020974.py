async def test_reconfigure_fails(
    hass: HomeAssistant,
    mock_serial_bridge: AsyncMock,
    mock_serial_bridge_config_entry: MockConfigEntry,
    side_effect: Exception,
    error: str,
) -> None:
    """Test that the host can be reconfigured."""
    mock_serial_bridge_config_entry.add_to_hass(hass)
    result = await mock_serial_bridge_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_serial_bridge.login.side_effect = side_effect

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.100.60",
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
        },
    )

    assert reconfigure_result["type"] is FlowResultType.FORM
    assert reconfigure_result["step_id"] == "reconfigure"
    assert reconfigure_result["errors"] == {"base": error}

    mock_serial_bridge.login.side_effect = None

    reconfigure_result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.100.61",
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
        },
    )

    assert reconfigure_result["type"] is FlowResultType.ABORT
    assert reconfigure_result["reason"] == "reconfigure_successful"
    assert mock_serial_bridge_config_entry.data == {
        CONF_HOST: "192.168.100.61",
        CONF_PORT: BRIDGE_PORT,
        CONF_PIN: BRIDGE_PIN,
        CONF_TYPE: BRIDGE,
    }