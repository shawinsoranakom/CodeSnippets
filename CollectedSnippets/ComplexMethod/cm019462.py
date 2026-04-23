async def test_user_usb_success(hass: HomeAssistant) -> None:
    """Test user usb step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result.get("flow_id"),
        {"next_step_id": "usbselect"},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PORT: USB_DEV,
        },
    )
    assert result
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "vlp"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Velbus USB"
    data = result.get("data")
    assert data
    assert data[CONF_PORT] == PORT_SERIAL