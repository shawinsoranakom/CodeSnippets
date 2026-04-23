async def test_config_flow_manual_error_could_not_find_motor(
    hass: HomeAssistant,
    motionblinds_ble_connect: tuple[AsyncMock, Mock],
    mac_code: str,
    local_name: str,
    display_name: str,
    address: str,
    blind_type: MotionBlindType,
) -> None:
    """Could not find motor error flow manually initialized by the user."""

    # Initialize
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # Try with MAC code that cannot be found
    motionblinds_ble_connect[1].name = "WRONG_NAME"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: mac_code},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": const.ERROR_COULD_NOT_FIND_MOTOR}

    # Recover
    motionblinds_ble_connect[1].name = local_name
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