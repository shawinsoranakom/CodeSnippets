async def test_options_flow(
    hass: HomeAssistant,
    setup_integration: ComponentSetup,
    config_entry: MockConfigEntry,
) -> None:
    """Test options flow."""
    await setup_integration()
    assert not config_entry.options

    # Trigger options flow, first time
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    data_schema = result["data_schema"].schema
    assert set(data_schema) == {"language_code"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"language_code": "es-ES"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"language_code": "es-ES"}

    # Retrigger options flow, not change language
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    data_schema = result["data_schema"].schema
    assert set(data_schema) == {"language_code"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"language_code": "es-ES"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"language_code": "es-ES"}

    # Retrigger options flow, change language
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    data_schema = result["data_schema"].schema
    assert set(data_schema) == {"language_code"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"language_code": "en-US"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"language_code": "en-US"}