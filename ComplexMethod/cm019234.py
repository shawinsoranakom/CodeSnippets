async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_immich: Mock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: "https://localhost:8443", CONF_VERIFY_SSL: True},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "localhost"
    assert mock_config_entry.data[CONF_PORT] == 8443
    assert mock_config_entry.data[CONF_SSL] is True
    assert mock_config_entry.data[CONF_VERIFY_SSL] is True