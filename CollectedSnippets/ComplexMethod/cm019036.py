async def test_alexa_config_migrate_expose_entity_prefs_default(
    hass: HomeAssistant,
    cloud_prefs: CloudPreferences,
    cloud_stub: Mock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migrating Alexa entity config."""
    hass.set_state(CoreState.starting)

    assert await async_setup_component(hass, "homeassistant", {})

    binary_sensor_supported = entity_registry.async_get_or_create(
        "binary_sensor",
        "test",
        "binary_sensor_supported",
        original_device_class="door",
        suggested_object_id="supported",
    )

    binary_sensor_unsupported = entity_registry.async_get_or_create(
        "binary_sensor",
        "test",
        "binary_sensor_unsupported",
        original_device_class="battery",
        suggested_object_id="unsupported",
    )

    light = entity_registry.async_get_or_create(
        "light",
        "test",
        "unique",
        suggested_object_id="light",
    )

    sensor_supported = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "sensor_supported",
        original_device_class="temperature",
        suggested_object_id="supported",
    )

    sensor_unsupported = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "sensor_unsupported",
        original_device_class="battery",
        suggested_object_id="unsupported",
    )

    water_heater = entity_registry.async_get_or_create(
        "water_heater",
        "test",
        "unique",
        suggested_object_id="water_heater",
    )

    await cloud_prefs.async_update(
        alexa_enabled=True,
        alexa_report_state=False,
        alexa_settings_version=1,
    )

    cloud_prefs._prefs[PREF_ALEXA_DEFAULT_EXPOSE] = [
        "binary_sensor",
        "light",
        "sensor",
        "water_heater",
    ]
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs, cloud_stub
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert async_get_entity_settings(hass, binary_sensor_supported.entity_id) == {
        "cloud.alexa": {"should_expose": True}
    }
    assert async_get_entity_settings(hass, binary_sensor_unsupported.entity_id) == {
        "cloud.alexa": {"should_expose": False}
    }
    assert async_get_entity_settings(hass, light.entity_id) == {
        "cloud.alexa": {"should_expose": True}
    }
    assert async_get_entity_settings(hass, sensor_supported.entity_id) == {
        "cloud.alexa": {"should_expose": True}
    }
    assert async_get_entity_settings(hass, sensor_unsupported.entity_id) == {
        "cloud.alexa": {"should_expose": False}
    }
    assert async_get_entity_settings(hass, water_heater.entity_id) == {
        "cloud.alexa": {"should_expose": False}
    }