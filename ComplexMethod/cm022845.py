async def test_usb_discovery(
    hass: HomeAssistant,
) -> None:
    """Test usb discovery success path."""
    usb_discovery_info = UsbServiceInfo(
        device="/dev/enocean0",
        pid="6001",
        vid="0403",
        serial_number="1234",
        description="USB 300",
        manufacturer="EnOcean GmbH",
    )
    device = "/dev/enocean0"
    # test discovery step
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USB},
        data=usb_discovery_info,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "usb_confirm"
    assert result["errors"] is None

    # test device path
    with (
        patch(
            GATEWAY_CLASS,
            return_value=Mock(start=AsyncMock(), stop=Mock()),
        ),
        patch(SETUP_ENTRY_METHOD, AsyncMock(return_value=True)),
        patch(
            "homeassistant.components.usb.get_serial_by_id",
            side_effect=lambda x: x,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MANUFACTURER
    assert result["data"] == {"device": device}
    assert result["context"]["unique_id"] == "0403:6001_1234_EnOcean GmbH_USB 300"
    assert result["context"]["title_placeholders"] == {
        "name": "USB 300 - /dev/enocean0, s/n: 1234 - EnOcean GmbH - 0403:6001"
    }
    assert result["result"].state is ConfigEntryState.LOADED