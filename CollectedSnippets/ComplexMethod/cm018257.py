async def test_config_flow_gateway_cloud_multiple_success(hass: HomeAssistant) -> None:
    """Test a successful config flow using cloud with multiple devices."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.xiaomi_miio.config_flow.MiCloud.get_devices",
        return_value=TEST_CLOUD_DEVICES_2,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                const.CONF_CLOUD_USERNAME: TEST_CLOUD_USER,
                const.CONF_CLOUD_PASSWORD: TEST_CLOUD_PASS,
                const.CONF_CLOUD_COUNTRY: TEST_CLOUD_COUNTRY,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"select_device": f"{TEST_NAME2} - {TEST_MODEL}"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_NAME2
    assert result["data"] == {
        const.CONF_FLOW_TYPE: const.CONF_GATEWAY,
        const.CONF_CLOUD_USERNAME: TEST_CLOUD_USER,
        const.CONF_CLOUD_PASSWORD: TEST_CLOUD_PASS,
        const.CONF_CLOUD_COUNTRY: TEST_CLOUD_COUNTRY,
        CONF_HOST: TEST_HOST2,
        CONF_TOKEN: TEST_TOKEN,
        CONF_MODEL: TEST_MODEL,
        CONF_MAC: TEST_MAC2,
    }