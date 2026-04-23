async def test_reconfigure_flow_auth_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_nrgkick_api: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test reconfiguration auth step errors and recovery."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    mock_nrgkick_api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.200"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure_auth"

    mock_nrgkick_api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure_auth"
    assert result["errors"] == {"base": error}

    mock_nrgkick_api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"