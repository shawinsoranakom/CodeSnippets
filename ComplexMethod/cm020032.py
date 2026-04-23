async def test_config_flow_user_success(hass: HomeAssistant) -> None:
    """Test a successful config flow initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

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

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_PORT: TEST_PORT,
        CONF_MAC: TEST_MAC,
        const.CONF_INTERFACE: config_flow.DEFAULT_INTERFACE,
        CONF_PROTOCOL: TEST_PROTOCOL,
        const.CONF_KEY: TEST_KEY,
        const.CONF_SID: TEST_SID,
    }