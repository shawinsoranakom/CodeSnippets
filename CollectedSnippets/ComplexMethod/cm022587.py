async def test_user_step_fail_with_error(
    hass: HomeAssistant,
    mock_lunatone_info: AsyncMock,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test user step with an error."""
    mock_lunatone_info.async_update.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: BASE_URL},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    mock_lunatone_info.async_update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: BASE_URL},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == BASE_URL
    assert result["data"] == {CONF_URL: BASE_URL}