async def test_flow_unlock_works(hass: HomeAssistant) -> None:
    """Test we finish a config flow with an unlock request."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.is_locked = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "unlock"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"unlock": True},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": device.name},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == device.name
    assert result["data"] == device.get_entry_data()

    assert mock_api.set_lock.call_args == call(False)
    assert mock_api.set_lock.call_count == 1