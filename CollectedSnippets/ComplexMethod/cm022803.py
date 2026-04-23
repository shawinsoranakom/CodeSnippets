async def test_import_expose_settings_2(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    target_domain: Platform,
) -> None:
    """Test importing assistant expose settings.

    This tests the expose settings are only copied from the source device when the
    switch_as_x config entry is setup the first time.
    """

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

    # Register the switch as x entity in the entity registry, this means
    # the entity has been setup before
    switch_as_x_entity_entry = entity_registry.async_get_or_create(
        target_domain,
        "switch_as_x",
        switch_as_x_config_entry.entry_id,
        suggested_object_id="abc",
    )
    for assistant, should_expose in EXPOSE_SETTINGS.items():
        exposed_entities.async_expose_entity(
            hass, assistant, switch_as_x_entity_entry.entity_id, not should_expose
        )

    assert await hass.config_entries.async_setup(switch_as_x_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_entry = entity_registry.async_get(f"{target_domain}.abc")
    assert entity_entry

    # Check switch_as_x expose settings were not copied from the switch
    expose_settings = exposed_entities.async_get_entity_settings(
        hass, entity_entry.entity_id
    )
    for assistant, settings in EXPOSE_SETTINGS.items():
        assert expose_settings[assistant]["should_expose"] is not settings

    # Check the switch settings were not modified
    expose_settings = exposed_entities.async_get_entity_settings(
        hass, switch_entity_entry.entity_id
    )
    for assistant, settings in EXPOSE_SETTINGS.items():
        assert expose_settings[assistant]["should_expose"] == settings