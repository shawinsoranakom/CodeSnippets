async def test_reconfigure_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_airobot_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    error_base: str,
) -> None:
    """Test reconfiguration flow with errors."""
    mock_config_entry.add_to_hass(hass)

    # Trigger reconfiguration
    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # First attempt with error
    mock_airobot_client.get_statuses.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.200",
            CONF_USERNAME: "T01A1B2C3",
            CONF_PASSWORD: "wrong-password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_base}

    # Recover from error
    mock_airobot_client.get_statuses.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.200",
            CONF_USERNAME: "T01A1B2C3",
            CONF_PASSWORD: "new-password",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.200"
    assert mock_config_entry.data[CONF_PASSWORD] == "new-password"