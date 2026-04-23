async def test_config_flow_step_device_manual_model_succes(hass: HomeAssistant) -> None:
    """Test config flow, device connection error, manual model."""
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

    error = DeviceException({})
    error.__cause__ = ChecksumError({})
    with patch(
        "homeassistant.components.xiaomi_miio.device.Device.info",
        side_effect=error,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "connect"
    assert result["errors"] == {"base": "wrong_token"}

    overwrite_model = const.MODELS_VACUUM[0]

    with patch(
        "homeassistant.components.xiaomi_miio.device.Device.info",
        side_effect=DeviceException({}),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_MODEL: overwrite_model},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == overwrite_model
    assert result["data"] == {
        const.CONF_FLOW_TYPE: CONF_DEVICE,
        const.CONF_CLOUD_USERNAME: None,
        const.CONF_CLOUD_PASSWORD: None,
        const.CONF_CLOUD_COUNTRY: None,
        CONF_HOST: TEST_HOST,
        CONF_TOKEN: TEST_TOKEN,
        CONF_MODEL: overwrite_model,
        CONF_MAC: None,
    }