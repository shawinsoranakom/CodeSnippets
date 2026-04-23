async def test_alexa_update_expose_trigger_sync(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    cloud_prefs: CloudPreferences,
    cloud_stub: Mock,
) -> None:
    """Test Alexa config responds to updating exposed entities."""
    assert await async_setup_component(hass, "homeassistant", {})
    # Enable exposing new entities to Alexa
    expose_new(hass, True)
    # Register entities
    binary_sensor_entry = entity_registry.async_get_or_create(
        "binary_sensor", "test", "unique", suggested_object_id="door"
    )
    sensor_entry = entity_registry.async_get_or_create(
        "sensor", "test", "unique", suggested_object_id="temp"
    )
    light_entry = entity_registry.async_get_or_create(
        "light", "test", "unique", suggested_object_id="kitchen"
    )

    hass.states.async_set(binary_sensor_entry.entity_id, "on")
    hass.states.async_set(
        sensor_entry.entity_id,
        "23",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )
    hass.states.async_set(light_entry.entity_id, "off")

    await cloud_prefs.async_update(
        alexa_enabled=True,
        alexa_report_state=False,
    )
    conf = alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs, cloud_stub
    )
    await conf.async_initialize()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    with patch_sync_helper() as (to_update, to_remove):
        expose_entity(hass, light_entry.entity_id, True)
        await hass.async_block_till_done()
        async_fire_time_changed(hass, fire_all=True)
        await hass.async_block_till_done()

    assert conf._alexa_sync_unsub is None
    assert to_update == [light_entry.entity_id]
    assert to_remove == []

    with patch_sync_helper() as (to_update, to_remove):
        expose_entity(hass, light_entry.entity_id, False)
        expose_entity(hass, binary_sensor_entry.entity_id, True)
        expose_entity(hass, sensor_entry.entity_id, True)
        await hass.async_block_till_done()
        async_fire_time_changed(hass, fire_all=True)
        await hass.async_block_till_done()

    assert conf._alexa_sync_unsub is None
    assert sorted(to_update) == [binary_sensor_entry.entity_id, sensor_entry.entity_id]
    assert to_remove == [light_entry.entity_id]

    with patch_sync_helper() as (to_update, to_remove):
        await cloud_prefs.async_update(
            alexa_enabled=False,
        )
        await hass.async_block_till_done()

    assert conf._alexa_sync_unsub is None
    assert to_update == []
    assert to_remove == [
        binary_sensor_entry.entity_id,
        sensor_entry.entity_id,
        light_entry.entity_id,
    ]