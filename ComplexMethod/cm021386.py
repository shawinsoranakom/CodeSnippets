async def test_flow_user_works(hass: HomeAssistant) -> None:
    """Test a config flow initiated by the user.

    Best case scenario with no errors or locks.
    """
    device = get_device("Living Room")
    mock_api = device.get_mock_api()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(DEVICE_HELLO, return_value=mock_api) as mock_hello:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
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
    assert result["data"] == device.get_entry_data()

    assert mock_hello.call_count == 1
    assert mock_api.auth.call_count == 1