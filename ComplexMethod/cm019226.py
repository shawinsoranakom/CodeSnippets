async def test_config_flow_manual_error_invalid_mac(
    hass: HomeAssistant,
    mac_code: str,
    address: str,
    local_name: str,
    display_name: str,
    blind_type: MotionBlindType,
) -> None:
    """Invalid MAC code error flow manually initialized by the user."""

    # Initialize
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # Try invalid MAC code
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: "AABBCC"},  # A MAC code should be 4 characters
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": const.ERROR_INVALID_MAC_CODE}

    # Recover
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: mac_code},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    # Finish flow
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