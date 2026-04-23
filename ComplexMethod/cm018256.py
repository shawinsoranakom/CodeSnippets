async def test_config_flow_gateway_success(hass: HomeAssistant) -> None:
    """Test a successful config flow."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MANUAL: True},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_MODEL
    assert result["data"] == {
        const.CONF_FLOW_TYPE: const.CONF_GATEWAY,
        const.CONF_CLOUD_USERNAME: None,
        const.CONF_CLOUD_PASSWORD: None,
        const.CONF_CLOUD_COUNTRY: None,
        CONF_HOST: TEST_HOST,
        CONF_TOKEN: TEST_TOKEN,
        CONF_MODEL: TEST_MODEL,
        CONF_MAC: TEST_MAC,
    }