async def test_flow_import_works(hass: HomeAssistant) -> None:
    """Test an import flow."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api) as mock_hello:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": device.host},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "finish"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": device.name},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == device.name
    assert result["data"]["host"] == device.host
    assert result["data"]["mac"] == device.mac
    assert result["data"]["type"] == device.devtype

    assert mock_api.auth.call_count == 1
    assert mock_hello.call_count == 1