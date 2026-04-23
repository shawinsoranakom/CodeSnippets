async def test_config_flow_manual_success(
    hass: HomeAssistant,
    blind_type: MotionBlindType,
    mac_code: str,
    address: str,
    local_name: str,
    display_name: str,
) -> None:
    """Successful flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: mac_code},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_BLIND_TYPE: blind_type.name.lower()},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == display_name
    assert result["data"] == {
        CONF_ADDRESS: address,
        const.CONF_LOCAL_NAME: local_name,
        const.CONF_MAC_CODE: mac_code,
        const.CONF_BLIND_TYPE: blind_type.name.lower(),
    }
    assert result["options"] == {}