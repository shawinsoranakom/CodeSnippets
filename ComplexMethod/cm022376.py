async def test_connection_error_and_recovery(
    hass: HomeAssistant,
    mock_system_nexa_2_device: MagicMock,
    mock_setup_entry: AsyncMock,
    exception: type[Exception],
    error_key: str,
) -> None:
    """Test connection error handling and recovery."""
    mock_system_nexa_2_device.return_value.get_info.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_key}

    # Remove the side effect and retry - should succeed now
    device = mock_system_nexa_2_device.return_value
    device.get_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Outdoor Smart Plug (WPO-01)"
    assert len(mock_setup_entry.mock_calls) == 1