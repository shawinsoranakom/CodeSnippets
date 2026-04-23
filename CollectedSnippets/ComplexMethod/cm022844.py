async def test_reconfigure_flow_cannot_connect(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_request_status: AsyncMock,
) -> None:
    """Test reconfiguration with connection error and recovery."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # New configuration data with different host/port.
    new_conf_data = {CONF_HOST: "new_host", CONF_PORT: 4321}
    mock_request_status.side_effect = OSError()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=new_conf_data
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"

    # Test recovery by fixing the connection issue.
    mock_request_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=new_conf_data
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == new_conf_data