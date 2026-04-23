async def test_hassio_addon_discovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_pythonkuma: AsyncMock,
) -> None:
    """Test config flow initiated by Supervisor."""
    mock_pythonkuma.metrics.side_effect = [UptimeKumaAuthenticationException, None]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_SERVICE_INFO,
        context={"source": SOURCE_HASSIO},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hassio_confirm"
    assert result["description_placeholders"] == {"addon": "Uptime Kuma"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "apikey"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "a0d7b954_uptime-kuma"
    assert result["data"] == {
        CONF_URL: "http://localhost:3001/",
        CONF_VERIFY_SSL: True,
        CONF_API_KEY: "apikey",
    }

    assert len(mock_setup_entry.mock_calls) == 1