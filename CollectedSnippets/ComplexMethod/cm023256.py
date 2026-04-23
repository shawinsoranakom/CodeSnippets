async def test_usb_discovery_with_existing_usb_flow(hass: HomeAssistant) -> None:
    """Test usb discovery allows more than one USB flow in progress."""
    first_usb_info = UsbServiceInfo(
        device="/dev/other_device",
        pid="AAAA",
        vid="AAAA",
        serial_number="5678",
        description="zwave radio",
        manufacturer="test",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USB},
        data=first_usb_info,
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "installation_type"

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USB},
        data=USB_DISCOVERY_INFO,
    )
    assert result2["type"] is FlowResultType.MENU
    assert result2["step_id"] == "installation_type"

    usb_flows_in_progress = hass.config_entries.flow.async_progress_by_handler(
        DOMAIN, match_context={"source": config_entries.SOURCE_USB}
    )

    assert len(usb_flows_in_progress) == 2

    for flow in (result, result2):
        hass.config_entries.flow.async_abort(flow["flow_id"])

    assert len(hass.config_entries.flow.async_progress()) == 0