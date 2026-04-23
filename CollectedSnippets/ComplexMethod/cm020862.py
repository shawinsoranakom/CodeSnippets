async def test_form_invalid_com_ports(hass: HomeAssistant) -> None:
    """Test we display correct info when the comport is invalid.."""

    fakecomports = []
    fakecomports.append(
        SerialDevice(
            device="/dev/ttyUSB7",
            serial_number=None,
            manufacturer=None,
            description=None,
        )
    )
    with patch(
        "homeassistant.components.aurora_abb_powerone.config_flow.usb.async_scan_serial_ports",
        return_value=fakecomports,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "aurorapy.client.AuroraSerialClient.connect",
        side_effect=OSError(19, "...no such device..."),
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: "/dev/ttyUSB7", CONF_ADDRESS: 7},
        )
    assert result2["errors"] == {"base": "invalid_serial_port"}

    with patch(
        "aurorapy.client.AuroraSerialClient.connect",
        side_effect=AuroraError("..could not open port..."),
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: "/dev/ttyUSB7", CONF_ADDRESS: 7},
        )
    assert result2["errors"] == {"base": "cannot_open_serial_port"}

    with patch(
        "aurorapy.client.AuroraSerialClient.connect",
        side_effect=AuroraTimeoutError("...No response after..."),
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: "/dev/ttyUSB7", CONF_ADDRESS: 7},
        )
    assert result2["errors"] == {"base": "cannot_connect"}

    with (
        patch(
            "aurorapy.client.AuroraSerialClient.connect",
            side_effect=AuroraError("...Some other message!!!123..."),
            return_value=None,
        ),
        patch(
            "serial.Serial.isOpen",
            return_value=True,
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.close",
        ) as mock_clientclose,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: "/dev/ttyUSB7", CONF_ADDRESS: 7},
        )
    assert result2["errors"] == {"base": "cannot_connect"}
    assert len(mock_clientclose.mock_calls) == 1