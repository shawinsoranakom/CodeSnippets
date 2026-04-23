async def test_setup_network_rfxtrx(
    hass: HomeAssistant,
    dsmr_connection_send_validate_fixture: tuple[MagicMock, MagicMock, MagicMock],
    rfxtrx_dsmr_connection_send_validate_fixture: tuple[
        MagicMock, MagicMock, MagicMock
    ],
) -> None:
    """Test we can setup network."""
    (_connection_factory, _transport, protocol) = dsmr_connection_send_validate_fixture

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"type": "Network"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_network"
    assert result["errors"] == {}

    # set-up DSMRProtocol to yield no valid telegram, this will retry with RFXtrxDSMRProtocol
    protocol.telegram = {}

    with patch("homeassistant.components.dsmr.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "10.10.0.1",
                "port": 1234,
                "dsmr_version": "2.2",
            },
        )
        await hass.async_block_till_done()

    entry_data = {
        "host": "10.10.0.1",
        "port": 1234,
        "dsmr_version": "2.2",
        "protocol": "rfxtrx_dsmr_protocol",
    }

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.10.0.1:1234"
    assert result["data"] == {**entry_data, **SERIAL_DATA}