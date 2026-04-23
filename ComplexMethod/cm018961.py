async def test_reconfigure_flow_config_unchanged_loaded(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure skips connection testing if loaded config is unchanged."""
    await setup_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert mock_config_entry.state is ConfigEntryState.LOADED

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], dict(mock_config_entry.data)
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == MOCK_CONFIG_DATA
    assert mock_satel.connect.call_count == 0

    await hass.async_block_till_done()
    assert mock_setup_entry.call_count == 1