async def test_form_exceptions_user(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_panel: AsyncMock,
    config_flow_data: dict[str, Any],
    exception: Exception,
    message: str,
) -> None:
    """Test we handle exceptions correctly."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.1.1.1", CONF_PORT: 7700},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert result["errors"] == {}
    mock_panel.connect.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], config_flow_data
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert result["errors"] == {"base": message}

    mock_panel.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], config_flow_data
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY