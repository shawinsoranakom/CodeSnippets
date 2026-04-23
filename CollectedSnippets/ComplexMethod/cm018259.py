async def test_config_flow_gateway_cloud_no_devices(hass: HomeAssistant) -> None:
    """Test a failed config flow using cloud with no devices."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.xiaomi_miio.config_flow.MiCloud.get_devices",
        return_value=[],
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
    assert result["errors"] == {"base": "cloud_no_devices"}

    with patch(
        "homeassistant.components.xiaomi_miio.config_flow.MiCloud.get_devices",
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