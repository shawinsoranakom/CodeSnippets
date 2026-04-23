async def test_errors_and_flow_recovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_lhm_client: AsyncMock,
    side_effect: Exception,
    error_text: str,
) -> None:
    """Test that errors are shown as expected."""
    mock_lhm_client.get_data.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_CONFIG
    )

    assert result["errors"] == {"base": error_text}
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_lhm_client.get_data.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_CONFIG
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_setup_entry.call_count == 1