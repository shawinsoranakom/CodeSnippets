async def test_flow_reconfigure_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_pythonkuma: AsyncMock,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test reconfigure flow errors and recover."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_pythonkuma.metrics.side_effect = raise_error

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://uptime.example.org:3001/",
            CONF_VERIFY_SSL: False,
            CONF_API_KEY: "newapikey",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    mock_pythonkuma.metrics.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://uptime.example.org:3001/",
            CONF_VERIFY_SSL: False,
            CONF_API_KEY: "newapikey",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data == {
        CONF_URL: "https://uptime.example.org:3001/",
        CONF_VERIFY_SSL: False,
        CONF_API_KEY: "newapikey",
    }

    assert len(hass.config_entries.async_entries()) == 1