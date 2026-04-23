async def test_config_flow_step_device_manual_model_error(hass: HomeAssistant) -> None:
    """Test config flow, device connection error, model None."""
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

    with patch(
        "homeassistant.components.xiaomi_miio.device.Device.info",
        return_value=get_mock_info(model=None),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "connect"
    assert result["errors"] == {"base": "cannot_connect"}

    with patch(
        "homeassistant.components.xiaomi_miio.device.Device.info",
        side_effect=Exception({}),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_MODEL: TEST_MODEL},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unknown"