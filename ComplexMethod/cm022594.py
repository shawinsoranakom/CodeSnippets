async def test_form_errors_with_recovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_liebherr_client: MagicMock,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test error handling with successful recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {}

    # Trigger error
    mock_liebherr_client.get_devices.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": expected_error}

    # Recover and complete successfully
    mock_liebherr_client.get_devices.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Liebherr"
    assert result.get("data") == MOCK_USER_INPUT