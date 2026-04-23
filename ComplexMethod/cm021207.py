async def test_flow_usb(hass: HomeAssistant) -> None:
    """Test usb flow connection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USB}, data=DISCOVERY_INFO
    )
    assert result
    assert result.get("type") is FlowResultType.FORM
    assert not result.get("errors")
    assert result.get("flow_id")
    assert result.get("step_id") == "meters"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_MAC: [METER_LIST.meter_mac_ids[0].hex()]}
    )
    assert result
    assert result.get("type") is FlowResultType.CREATE_ENTRY