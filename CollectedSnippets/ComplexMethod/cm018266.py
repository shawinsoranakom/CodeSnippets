async def zeroconf_device_success(
    hass: HomeAssistant, zeroconf_name_to_test: str, model_to_test: str
) -> None:
    """Test a successful zeroconf discovery of a device  (base class)."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(TEST_HOST),
            ip_addresses=[ip_address(TEST_HOST)],
            hostname="mock_hostname",
            name=zeroconf_name_to_test,
            port=None,
            properties={"poch": f"0:mac={TEST_MAC_DEVICE}\x00"},
            type="mock_type",
        ),
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

    mock_info = get_mock_info(model=model_to_test)

    with patch(
        "homeassistant.components.xiaomi_miio.device.Device.info",
        return_value=mock_info,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_TOKEN: TEST_TOKEN},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == model_to_test
    assert result["data"] == {
        const.CONF_FLOW_TYPE: CONF_DEVICE,
        const.CONF_CLOUD_USERNAME: None,
        const.CONF_CLOUD_PASSWORD: None,
        const.CONF_CLOUD_COUNTRY: None,
        CONF_HOST: TEST_HOST,
        CONF_TOKEN: TEST_TOKEN,
        CONF_MODEL: model_to_test,
        CONF_MAC: TEST_MAC,
    }