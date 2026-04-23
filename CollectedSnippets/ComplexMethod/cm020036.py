async def test_config_flow_user_invalid_key(hass: HomeAssistant) -> None:
    """Test a failed config flow initialized by the user with an invalid key."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_gateway_discovery = get_mock_discovery([TEST_HOST], invalid_key=True)

    with patch(
        "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGatewayDiscovery",
        return_value=mock_gateway_discovery,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "settings"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_KEY: TEST_KEY, CONF_NAME: TEST_NAME},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "settings"
    assert result["errors"] == {const.CONF_KEY: "invalid_key"}