async def test_reconfigure_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_saunum_client_class,
    side_effect: Exception,
    error_base: str,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test reconfigure flow error handling."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_saunum_client_class.create.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_RECONFIGURE_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_base}

    # Test recovery - try again without the error
    mock_saunum_client_class.create.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_RECONFIGURE_INPUT,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == TEST_RECONFIGURE_INPUT