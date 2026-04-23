async def test_reauth_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_lhm_client: AsyncMock,
    side_effect: Exception,
    error_text: str,
) -> None:
    """Test reauth flow errors."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_lhm_client.get_data.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        REAUTH_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_text}

    mock_lhm_client.get_data.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        REAUTH_INPUT,
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data == {**VALID_CONFIG, **REAUTH_INPUT}
    assert len(hass.config_entries.async_entries()) == 1