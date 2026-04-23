async def test_show_config_form_api_method_no_auth_token(
    hass: HomeAssistant, webhook_id
) -> None:
    """Test show configuration form."""

    # Using Keg
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Keg,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "api_method"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOKEN: ""}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "api_method"
    assert len(result["errors"]) == 1
    assert result["errors"]["base"] == "no_auth_token"

    # Using Airlock
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "api_method"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOKEN: ""}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "api_method"
    assert len(result["errors"]) == 1
    assert result["errors"]["base"] == "no_api_method"