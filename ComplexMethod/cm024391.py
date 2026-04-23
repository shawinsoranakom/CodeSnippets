async def test_reconfigure_flow_no_change(
    hass: HomeAssistant,
    mock_hdfury_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfiguration without changing values."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {}

    # Original entry
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.123"
    assert mock_config_entry.unique_id == "000123456789"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.123",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Changed entry
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.123"
    assert mock_config_entry.unique_id == "000123456789"