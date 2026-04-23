async def test_manual_entry(mock_heat_meter, hass: HomeAssistant) -> None:
    """Test manual entry."""

    mock_heat_meter().read.return_value = MockUltraheatRead("LUGCUH50", "123456789")

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

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "LUGCUH50"
    assert result["data"] == {
        "device": "/dev/ttyUSB0",
        "model": "LUGCUH50",
        "device_number": "123456789",
    }