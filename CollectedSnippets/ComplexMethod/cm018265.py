async def config_flow_generic_roborock(hass: HomeAssistant) -> None:
    """Test a successful config flow for a generic roborock vacuum."""
    dummy_model = "roborock.vacuum.dummy"

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

    mock_info = get_mock_info(model=dummy_model)

    with patch(
        "homeassistant.components.xiaomi_miio.device.Device.info",
        return_value=mock_info,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == dummy_model
    assert result["data"] == {
        const.CONF_FLOW_TYPE: CONF_DEVICE,
        const.CONF_CLOUD_USERNAME: None,
        const.CONF_CLOUD_PASSWORD: None,
        const.CONF_CLOUD_COUNTRY: None,
        CONF_HOST: TEST_HOST,
        CONF_TOKEN: TEST_TOKEN,
        CONF_MODEL: dummy_model,
        CONF_MAC: TEST_MAC,
    }