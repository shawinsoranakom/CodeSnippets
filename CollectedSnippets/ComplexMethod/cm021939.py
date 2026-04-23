async def test_reconfigure_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_pyloadapi: AsyncMock,
    side_effect: Exception,
    error_text: str,
) -> None:
    """Test reconfiguration flow."""

    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_pyloadapi.get_status.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_text}

    mock_pyloadapi.get_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data == USER_INPUT
    assert len(hass.config_entries.async_entries()) == 1