async def test_reconfigure_flow_config_unchanged_not_loaded(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure validates unchanged config if the entry is not loaded."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], dict(mock_config_entry.data)
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == MOCK_CONFIG_DATA
    assert mock_satel.connect.call_count == 1
    assert mock_setup_entry.call_count == 1