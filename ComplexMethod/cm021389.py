async def test_flow_reauth_works(hass: HomeAssistant) -> None:
    """Test a reauthentication flow."""
    device = get_device("Living Room")
    mock_entry = device.get_mock_entry()
    mock_entry.add_to_hass(hass)
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.AuthenticationError()

    with patch(DEVICE_FACTORY, return_value=mock_api):
        result = await mock_entry.start_reauth_flow(hass, data={"name": device.name})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reset"

    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api) as mock_hello:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    assert dict(mock_entry.data) == device.get_entry_data()
    assert mock_api.auth.call_count == 1
    assert mock_hello.call_count == 1