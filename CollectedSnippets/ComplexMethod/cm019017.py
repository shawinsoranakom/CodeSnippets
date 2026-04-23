async def test_google_config_migrate_expose_entity_prefs(
    hass: HomeAssistant,
    cloud_prefs: CloudPreferences,
    entity_registry: er.EntityRegistry,
    google_settings_version: int,
) -> None:
    """Test migrating Google entity config."""
    hass.set_state(CoreState.not_running)

    assert await async_setup_component(hass, "homeassistant", {})
    hass.states.async_set("light.state_only", "on")
    entity_exposed = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_exposed",
        suggested_object_id="exposed",
    )

    entity_no_2fa_exposed = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_no_2fa_exposed",
        suggested_object_id="no_2fa_exposed",
    )

    entity_migrated = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_migrated",
        suggested_object_id="migrated",
    )

    entity_config = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_config",
        suggested_object_id="config",
        entity_category=EntityCategory.CONFIG,
    )

    entity_default = entity_registry.async_get_or_create(
        "light",
        "test",
        "light_default",
        suggested_object_id="default",
    )

    entity_blocked = entity_registry.async_get_or_create(
        "group",
        "test",
        "group_all_locks",
        suggested_object_id="all_locks",
    )
    assert entity_blocked.entity_id == "group.all_locks"

    await cloud_prefs.async_update(
        google_enabled=True,
        google_report_state=False,
        google_settings_version=google_settings_version,
    )
    expose_entity(hass, entity_migrated.entity_id, False)

    cloud_prefs._prefs[PREF_GOOGLE_ENTITY_CONFIGS]["light.unknown"] = {
        PREF_SHOULD_EXPOSE: True,
        PREF_DISABLE_2FA: True,
    }
    cloud_prefs._prefs[PREF_GOOGLE_ENTITY_CONFIGS]["light.state_only"] = {
        PREF_SHOULD_EXPOSE: False
    }
    cloud_prefs._prefs[PREF_GOOGLE_ENTITY_CONFIGS][entity_exposed.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    cloud_prefs._prefs[PREF_GOOGLE_ENTITY_CONFIGS][entity_no_2fa_exposed.entity_id] = {
        PREF_SHOULD_EXPOSE: True,
        PREF_DISABLE_2FA: True,
    }
    cloud_prefs._prefs[PREF_GOOGLE_ENTITY_CONFIGS][entity_migrated.entity_id] = {
        PREF_SHOULD_EXPOSE: True
    }
    conf = CloudGoogleConfig(
        hass, GACTIONS_SCHEMA({}), "mock-user-id", cloud_prefs, Mock(is_logged_in=False)
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert async_get_entity_settings(hass, "light.unknown") == {
        "cloud.google_assistant": {"disable_2fa": True, "should_expose": True}
    }
    assert async_get_entity_settings(hass, "light.state_only") == {
        "cloud.google_assistant": {"should_expose": False}
    }
    assert async_get_entity_settings(hass, entity_exposed.entity_id) == {
        "cloud.google_assistant": {"should_expose": True}
    }
    assert async_get_entity_settings(hass, entity_migrated.entity_id) == {
        "cloud.google_assistant": {"should_expose": True}
    }
    assert async_get_entity_settings(hass, entity_no_2fa_exposed.entity_id) == {
        "cloud.google_assistant": {"disable_2fa": True, "should_expose": True}
    }
    assert async_get_entity_settings(hass, entity_config.entity_id) == {
        "cloud.google_assistant": {"should_expose": False}
    }
    assert async_get_entity_settings(hass, entity_default.entity_id) == {
        "cloud.google_assistant": {"should_expose": True}
    }
    assert async_get_entity_settings(hass, entity_blocked.entity_id) == {
        "cloud.google_assistant": {"should_expose": False}
    }