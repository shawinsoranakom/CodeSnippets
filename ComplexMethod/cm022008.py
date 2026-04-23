async def test_flow_works(hass: HomeAssistant, mock_panel) -> None:
    """Test config flow ."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_panel.get_status.return_value = {
        "mac": "11:22:33:44:55:66",
        "model": "Konnected",
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"port": 1234, "host": "1.2.3.4"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "model": "Konnected Alarm Panel",
        "id": "112233445566",
        "host": "1.2.3.4",
        "port": 1234,
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] == "1.2.3.4"
    assert result["data"]["port"] == 1234
    assert result["data"]["model"] == "Konnected"
    assert len(result["data"]["access_token"]) == 20  # confirm generated token size
    assert result["data"]["default_options"] == config_flow.OPTIONS_SCHEMA(
        {config_flow.CONF_IO: {}}
    )