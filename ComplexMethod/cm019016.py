async def test_google_config_expose_entity_prefs(
    hass: HomeAssistant,
    mock_conf: CloudGoogleConfig,
    cloud_prefs: CloudPreferences,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test Google config should expose using prefs."""
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

    expose_new(hass, True)
    expose_entity(hass, entity_entry5.entity_id, False)

    state = State("light.kitchen", "on")
    state_config = State(entity_entry1.entity_id, "on")
    state_diagnostic = State(entity_entry2.entity_id, "on")
    state_hidden_integration = State(entity_entry3.entity_id, "on")
    state_hidden_user = State(entity_entry4.entity_id, "on")
    state_not_exposed = State(entity_entry5.entity_id, "on")
    state_exposed_default = State(entity_entry6.entity_id, "on")

    # an entity which is not in the entity registry can be exposed
    expose_entity(hass, "light.kitchen", True)
    assert mock_conf.should_expose(state)
    # categorized and hidden entities should not be exposed
    assert not mock_conf.should_expose(state_config)
    assert not mock_conf.should_expose(state_diagnostic)
    assert not mock_conf.should_expose(state_hidden_integration)
    assert not mock_conf.should_expose(state_hidden_user)
    # this has been hidden
    assert not mock_conf.should_expose(state_not_exposed)
    # exposed by default
    assert mock_conf.should_expose(state_exposed_default)

    expose_entity(hass, entity_entry5.entity_id, True)
    assert mock_conf.should_expose(state_not_exposed)

    expose_entity(hass, entity_entry5.entity_id, None)
    assert not mock_conf.should_expose(state_not_exposed)