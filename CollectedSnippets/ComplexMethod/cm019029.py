async def test_alexa_config_expose_entity_prefs(
    hass: HomeAssistant,
    cloud_prefs: CloudPreferences,
    cloud_stub: Mock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test Alexa config should expose using prefs."""
    assert await async_setup_component(hass, "homeassistant", {})
    entity_entry1 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_config_id",
        suggested_object_id="config_light",
        entity_category=EntityCategory.CONFIG,
    )
    entity_entry2 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_diagnostic_id",
        suggested_object_id="diagnostic_light",
        entity_category=EntityCategory.DIAGNOSTIC,
    )
    entity_entry3 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_hidden_integration_id",
        suggested_object_id="hidden_integration_light",
        hidden_by=er.RegistryEntryHider.INTEGRATION,
    )
    entity_entry4 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_hidden_user_id",
        suggested_object_id="hidden_user_light",
        hidden_by=er.RegistryEntryHider.USER,
    )
    entity_entry5 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_basement_id",
        suggested_object_id="basement",
    )
    entity_entry6 = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_entrance_id",
        suggested_object_id="entrance",
    )

    await cloud_prefs.async_update(
        alexa_enabled=True,
        alexa_report_state=False,
    )
    expose_new(hass, True)
    expose_entity(hass, entity_entry5.entity_id, False)
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs, cloud_stub
    )
    await conf.async_initialize()

    # an entity which is not in the entity registry can be exposed
    expose_entity(hass, "light.kitchen", True)
    assert conf.should_expose("light.kitchen")
    # categorized and hidden entities should not be exposed
    assert not conf.should_expose(entity_entry1.entity_id)
    assert not conf.should_expose(entity_entry2.entity_id)
    assert not conf.should_expose(entity_entry3.entity_id)
    assert not conf.should_expose(entity_entry4.entity_id)
    # this has been hidden
    assert not conf.should_expose(entity_entry5.entity_id)
    # exposed by default
    assert conf.should_expose(entity_entry6.entity_id)

    expose_entity(hass, entity_entry5.entity_id, True)
    assert conf.should_expose(entity_entry5.entity_id)

    expose_entity(hass, entity_entry5.entity_id, None)
    assert not conf.should_expose(entity_entry5.entity_id)

    assert "alexa" not in hass.config.components
    await hass.async_block_till_done()
    assert "alexa" in hass.config.components
    assert not conf.should_expose(entity_entry5.entity_id)