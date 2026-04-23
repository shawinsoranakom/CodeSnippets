async def test_setup_serial(com_mock, transport_mock, hass: HomeAssistant) -> None:
    """Test we can setup serial."""
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

    with patch("homeassistant.components.rfxtrx.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": port.device}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "RFXTRX"
    assert result["data"] == {
        "host": None,
        "port": None,
        "device": port.device,
        "automatic_add": False,
        "devices": {},
    }