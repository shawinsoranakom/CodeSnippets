async def test_form_exceptions(
    hass: HomeAssistant,
    exception1: Exception,
    error1: dict[str, str],
    exception2: Exception,
    error2: dict[str, str],
    mock_solarlog_connector: AsyncMock,
) -> None:
    """Test we can handle Form exceptions."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_solarlog_connector.test_connection.side_effect = exception1

    # tests with connection error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: HOST, CONF_HAS_PWD: False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == error1

    # tests with password error
    mock_solarlog_connector.test_connection.side_effect = None
    mock_solarlog_connector.test_extended_data_available.side_effect = exception2

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: HOST, CONF_HAS_PWD: True}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "password"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "pwd"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "password"
    assert result["errors"] == error2

    mock_solarlog_connector.test_extended_data_available.side_effect = None

    # tests with all provided
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "pwd"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"][CONF_PASSWORD] == "pwd"