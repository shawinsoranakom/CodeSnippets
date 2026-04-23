async def test_config_flow_manual_error_no_bluetooth_adapter(
    hass: HomeAssistant,
    mac_code: str,
) -> None:
    """No Bluetooth adapter error flow manually initialized by the user."""

    # Try step_user with zero Bluetooth adapters
    with patch(
        "homeassistant.components.motionblinds_ble.config_flow.bluetooth.async_scanner_count",
        return_value=0,
    ):
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == const.ERROR_NO_BLUETOOTH_ADAPTER

    # Try discovery with zero Bluetooth adapters
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.motionblinds_ble.config_flow.bluetooth.async_scanner_count",
        return_value=0,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {const.CONF_MAC_CODE: mac_code},
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == const.ERROR_NO_BLUETOOTH_ADAPTER