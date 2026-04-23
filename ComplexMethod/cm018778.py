async def test_user_flow_auth_errors(
    hass: HomeAssistant, mock_nrgkick_api: AsyncMock, exception: Exception, error: str
) -> None:
    """Test errors are handled and the flow can recover to CREATE_ENTRY."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_nrgkick_api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_auth"
    assert result["errors"] == {}

    mock_nrgkick_api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_auth"
    assert result["errors"] == {"base": error}

    mock_nrgkick_api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY