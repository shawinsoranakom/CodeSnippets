async def test_reconfigure_flow_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    error_key: str,
    mock_openrgb_client,
) -> None:
    """Test reconfiguration flow with various errors."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    mock_openrgb_client.client_class_mock.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 6743},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": error_key}

    # Test recovery from error
    mock_openrgb_client.client_class_mock.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 6743},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.100"
    assert mock_config_entry.data[CONF_PORT] == 6743