async def test_reconfigure_flow_with_credentials(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_nrgkick_api: AsyncMock,
) -> None:
    """Test reconfiguration flow when authentication is required."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_nrgkick_api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.200"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure_auth"

    mock_nrgkick_api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "new_user", CONF_PASSWORD: "new_pass"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.200"
    assert mock_config_entry.data[CONF_USERNAME] == "new_user"
    assert mock_config_entry.data[CONF_PASSWORD] == "new_pass"