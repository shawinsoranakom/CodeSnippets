async def test_setup_serial_manual(
    com_mock,
    hass: HomeAssistant,
    dsmr_connection_send_validate_fixture: tuple[MagicMock, MagicMock, MagicMock],
) -> None:
    """Test we can setup serial with manual entry."""
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

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"port": "Enter Manually", "dsmr_version": "2.2"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_serial_manual_path"
    assert result["errors"] is None

    with patch("homeassistant.components.dsmr.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"port": "/dev/ttyUSB0"}
        )
        await hass.async_block_till_done()

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "protocol": "dsmr_protocol",
    }

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "/dev/ttyUSB0"
    assert result["data"] == {**entry_data, **SERIAL_DATA}