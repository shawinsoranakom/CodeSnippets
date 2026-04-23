async def test_step_user(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_DIASPORA: DEFAULT_DIASPORA, CONF_LANGUAGE: DEFAULT_LANGUAGE},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].data[CONF_DIASPORA] == DEFAULT_DIASPORA
    assert entries[0].data[CONF_LANGUAGE] == DEFAULT_LANGUAGE
    assert entries[0].data[CONF_LATITUDE] == hass.config.latitude
    assert entries[0].data[CONF_LONGITUDE] == hass.config.longitude
    assert entries[0].data[CONF_ELEVATION] == hass.config.elevation
    assert entries[0].data[CONF_TIME_ZONE] == hass.config.time_zone