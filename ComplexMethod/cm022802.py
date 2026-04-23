async def test_import_expose_settings_1(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    target_domain: Platform,
) -> None:
    """Test importing assistant expose settings."""
    await async_setup_component(hass, "homeassistant", {})

    switch_entity_entry = entity_registry.async_get_or_create(
        "switch",
        "test",
        "unique",
        original_name="ABC",
    )
    for assistant, should_expose in EXPOSE_SETTINGS.items():
        exposed_entities.async_expose_entity(
            hass, assistant, switch_entity_entry.entity_id, should_expose
        )

    # Add the config entry
    switch_as_x_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: switch_entity_entry.id,
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        },
        title="ABC",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )
    switch_as_x_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(switch_as_x_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_entry = entity_registry.async_get(f"{target_domain}.abc")
    assert entity_entry

    # Check switch_as_x expose settings were copied from the switch
    expose_settings = exposed_entities.async_get_entity_settings(
        hass, entity_entry.entity_id
    )
    for assistant, settings in EXPOSE_SETTINGS.items():
        assert expose_settings[assistant]["should_expose"] == settings

    # Check the switch is no longer exposed
    expose_settings = exposed_entities.async_get_entity_settings(
        hass, switch_entity_entry.entity_id
    )
    for assistant in EXPOSE_SETTINGS:
        assert expose_settings[assistant]["should_expose"] is False