async def test_setup_serial_fail(
    com_mock,
    hass: HomeAssistant,
    dsmr_connection_send_validate_fixture: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    """Test failed serial connection."""
    (_connection_factory, transport, protocol) = dsmr_connection_send_validate_fixture

    port = com_port()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # override the mock to have it fail the first time and succeed after
    first_fail_connection_factory = AsyncMock(
        return_value=(transport, protocol),
        side_effect=chain([serial.SerialException], repeat(DEFAULT)),
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

    with patch(
        "homeassistant.components.dsmr.config_flow.create_dsmr_reader",
        first_fail_connection_factory,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"port": port.device, "dsmr_version": "2.2"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_serial"
    assert result["errors"] == {"base": "cannot_connect"}