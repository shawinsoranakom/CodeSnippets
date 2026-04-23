async def test_reconfigure(
    hass: HomeAssistant,
    eheimdigital_hub_mock: AsyncMock,
    mock_config_entry: MockConfigEntry,
    side_effect: Exception,
    error_value: str,
) -> None:
    """Test reconfigure flow."""
    await init_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == SOURCE_RECONFIGURE

    eheimdigital_hub_mock.return_value.connect.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_value}

    eheimdigital_hub_mock.return_value.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert (
        mock_config_entry.unique_id
        == eheimdigital_hub_mock.return_value.main.mac_address
    )