async def test_discovery_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_discovery: MagicMock,
    mock_gateway: MagicMock,
) -> None:
    """Test a successful discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "select_gateway"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": mock_gateway.gw_sn},
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == mock_gateway.name
    assert result.get("data") == {
        CONF_SERIAL_NUMBER: mock_gateway.gw_sn,
        CONF_HOST: mock_gateway.gw_ip,
        CONF_PORT: mock_gateway.port,
        CONF_NAME: mock_gateway.name,
        CONF_USERNAME: mock_gateway.username,
        CONF_PASSWORD: mock_gateway.passwd,
    }
    result_entry = result.get("result")
    assert result_entry is not None
    assert result_entry.unique_id == mock_gateway.gw_sn
    mock_setup_entry.assert_called_once()
    mock_gateway.connect.assert_awaited_once()
    mock_gateway.disconnect.assert_awaited_once()