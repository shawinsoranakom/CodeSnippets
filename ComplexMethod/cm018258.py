async def test_config_flow_gateway_cloud_login_error(hass: HomeAssistant) -> None:
    """Test a failed config flow using cloud login error."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.xiaomi_miio.config_flow.MiCloud.login",
        return_value=False,
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
    assert result["step_id"] == "cloud"
    assert result["errors"] == {"base": "cloud_login_error"}

    with patch(
        "homeassistant.components.xiaomi_miio.config_flow.MiCloud.login",
        side_effect=MiCloudAccessDenied({}),
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
    assert result["step_id"] == "cloud"
    assert result["errors"] == {"base": "cloud_login_error"}

    with patch(
        "homeassistant.components.xiaomi_miio.config_flow.MiCloud.login",
        side_effect=Exception({}),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                const.CONF_CLOUD_USERNAME: TEST_CLOUD_USER,
                const.CONF_CLOUD_PASSWORD: TEST_CLOUD_PASS,
                const.CONF_CLOUD_COUNTRY: TEST_CLOUD_COUNTRY,
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unknown"