async def test_discovery_via_usb(hass: HomeAssistant) -> None:
    """Test usb flow -- radio detected."""
    discovery_info = UsbServiceInfo(
        device="/dev/ttyZIGBEE",
        pid="AAAA",
        vid="AAAA",
        serial_number="1234",
        description="zigbee radio",
        manufacturer="test",
    )
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USB}, data=discovery_info
    )
    await hass.async_block_till_done()

    assert result1["type"] is FlowResultType.FORM
    assert result1["step_id"] == "confirm"

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"], user_input={}
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.MENU
    assert result2["step_id"] == "choose_setup_strategy"

    with patch("homeassistant.components.zha.async_setup_entry", return_value=True):
        result_setup = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={"next_step_id": config_flow.SETUP_STRATEGY_RECOMMENDED},
        )

        result3 = await consume_progress_flow(
            hass,
            flow_id=result_setup["flow_id"],
            valid_step_ids=("form_new_network",),
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "zigbee radio"
    assert result3["data"] == {
        "device": {
            "baudrate": 115200,
            "flow_control": None,
            "path": "/dev/ttyZIGBEE",
        },
        CONF_RADIO_TYPE: "znp",
    }