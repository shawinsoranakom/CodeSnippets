async def test_reconfigure_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test reconfiguration flow."""

    mock_config_entry.add_to_hass(hass)

    assert mock_config_entry.data[CONF_HOST] != "10.0.0.132"

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Test successful reconfiguration with new host
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.132"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "10.0.0.132"
    assert mock_config_entry.data[CONF_DEVICE_ID] == "aabbccddee02"
    assert mock_config_entry.data[CONF_MODEL] == "WPO-01"
    assert mock_config_entry.data[CONF_NAME] == "Outdoor Smart Plug"