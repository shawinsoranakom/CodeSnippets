async def test_setup_serial_wrong_telegram(
    com_mock,
    hass: HomeAssistant,
    dsmr_connection_send_validate_fixture: tuple[MagicMock, MagicMock, MagicMock],
    rfxtrx_dsmr_connection_send_validate_fixture: tuple[
        MagicMock, MagicMock, MagicMock
    ],
) -> None:
    """Test failed telegram data."""
    (_connection_factory, _transport, protocol) = dsmr_connection_send_validate_fixture
    (
        _rfxtrx_connection_factory,
        _transport,
        rfxtrx_protocol,
    ) = rfxtrx_dsmr_connection_send_validate_fixture

    port = com_port()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Serial"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_serial"
    assert result["errors"] == {}

    protocol.telegram = {}
    rfxtrx_protocol.telegram = {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"port": port.device, "dsmr_version": "2.2"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_serial"
    assert result["errors"] == {"base": "cannot_communicate"}