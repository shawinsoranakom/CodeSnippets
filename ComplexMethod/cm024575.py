async def test_manual_entry_fail(mock_heat_meter, hass: HomeAssistant) -> None:
    """Test manual entry fails."""

    mock_heat_meter().read.side_effect = serial.SerialException

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device": "Enter Manually"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_serial_manual_path"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"device": "/dev/ttyUSB0"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "setup_serial_manual_path"
    assert result["errors"] == {"base": "cannot_connect"}