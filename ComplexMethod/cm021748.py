async def test_reconfigure(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_google_weather_api: AsyncMock,
) -> None:
    """Test reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "new-api-key",
            SECTION_API_KEY_OPTIONS: {
                CONF_REFERRER: "new-referrer",
            },
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_API_KEY] == "new-api-key"
    assert mock_config_entry.data.get(CONF_REFERRER) == "new-referrer"
    assert len(mock_setup_entry.mock_calls) == 1