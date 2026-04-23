async def test_user_error(
    hass: HomeAssistant,
    mock_api: AsyncMock,
    mock_setup_entry: AsyncMock,
    error: Exception,
    expected: str,
) -> None:
    """Test we display errors in the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_api.async_authorize.side_effect = error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONF_DATA
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": expected}

    # Show we can recover from errors:
    mock_api.async_authorize.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONF_DATA
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"] == CONF_DATA
    assert len(mock_setup_entry.mock_calls) == 1