async def test_async_step_user_failed_auth(
    hass: HomeAssistant,
    exception: Exception,
    expected_error: str,
    mock_compit_api: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test user step with invalid authentication then success after error is cleared."""
    mock_compit_api.side_effect = [exception, True]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == config_entries.SOURCE_USER

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    # Test success after error is cleared
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == CONFIG_INPUT[CONF_EMAIL]
    assert result["data"] == CONFIG_INPUT
    assert len(mock_setup_entry.mock_calls) == 1