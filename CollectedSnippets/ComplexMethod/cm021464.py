async def test_reconfigure_flow_exceptions(
    hass: HomeAssistant,
    mock_mealie_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    error: str,
) -> None:
    """Test reconfigure flow errors."""
    await setup_integration(hass, mock_config_entry)
    mock_mealie_client.get_user_info.side_effect = exception

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "http://test:9090", CONF_API_TOKEN: "token"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": error}

    mock_mealie_client.get_user_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "http://test:9090", CONF_API_TOKEN: "token"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"