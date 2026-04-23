async def test_reconfigure_exceptions(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_google_weather_api: AsyncMock,
    api_exception: Exception,
    expected_error: str,
    expected_placeholders: dict[str, str],
) -> None:
    """Test reconfigure flow with exceptions."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM

    mock_google_weather_api.async_get_current_conditions.side_effect = api_exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "invalid-api-key",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}
    assert result["description_placeholders"] == expected_placeholders

    mock_google_weather_api.async_get_current_conditions.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "valid-api-key",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert len(mock_setup_entry.mock_calls) == 1