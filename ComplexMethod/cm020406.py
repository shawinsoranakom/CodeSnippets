async def test_setup_serial_fail(com_mock, transport_mock, hass: HomeAssistant) -> None:
    """Test setup serial failed connection."""
    transport_mock.return_value.connect.side_effect = RFXtrxTransportError
    port = com_port()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Serial"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_serial"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device": port.device}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_serial"
    assert result["errors"] == {"base": "cannot_connect"}