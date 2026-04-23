async def test_config_flow_options_change(
    hass: HomeAssistant,
    owm_client_mock: AsyncMock,
) -> None:
    """Test that the options form."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, unique_id="openweathermap_unique_id", data=CONFIG
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    new_language = "es"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MODE: DEFAULT_OWM_MODE, CONF_LANGUAGE: new_language},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        CONF_LANGUAGE: new_language,
        CONF_MODE: DEFAULT_OWM_MODE,
    }

    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    updated_language = "es"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_LANGUAGE: updated_language}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        CONF_LANGUAGE: updated_language,
        CONF_MODE: DEFAULT_OWM_MODE,
    }

    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED