async def test_reconfigure_flow_errors(
    hass: HomeAssistant,
    mock_madvr_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test error handling in reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Test CannotConnect error
    mock_madvr_client.open_connection.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100", CONF_PORT: 44077},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Test no_mac error
    mock_madvr_client.open_connection.side_effect = None
    mock_madvr_client.connected = True
    mock_madvr_client.mac_address = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100", CONF_PORT: 44077},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_mac"}

    # Ensure errors are recoverable
    mock_madvr_client.mac_address = MOCK_MAC
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100", CONF_PORT: 44077},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"