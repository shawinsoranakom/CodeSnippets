async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options config flow for tomorrowio."""
    user_config = _get_config_schema(hass, SOURCE_USER)(MIN_CONFIG)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=user_config,
        options={CONF_TIMESTEP: DEFAULT_TIMESTEP},
        source=SOURCE_USER,
        unique_id=_get_unique_id(hass, user_config),
        version=1,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)

    assert entry.options[CONF_TIMESTEP] == DEFAULT_TIMESTEP
    assert CONF_TIMESTEP not in entry.data

    result = await hass.config_entries.options.async_init(entry.entry_id, data=None)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_TIMESTEP: 1}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"][CONF_TIMESTEP] == 1
    assert entry.options[CONF_TIMESTEP] == 1