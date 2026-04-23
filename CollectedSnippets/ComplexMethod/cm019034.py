async def test_alexa_entity_registry_sync(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    cloud_prefs: CloudPreferences,
) -> None:
    """Test Alexa config responds to entity registry."""
    # Enable exposing new entities to Alexa
    expose_new(hass, True)

    await alexa_config.CloudAlexaConfig(
        hass, ALEXA_SCHEMA({}), "mock-user-id", cloud_prefs, hass.data[DATA_CLOUD]
    ).async_initialize()

    with patch_sync_helper() as (to_update, to_remove):
        entry = entity_registry.async_get_or_create(
            "light", "test", "unique", suggested_object_id="kitchen"
        )
        await hass.async_block_till_done()

    assert to_update == [entry.entity_id]
    assert to_remove == []

    with patch_sync_helper() as (to_update, to_remove):
        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "remove", "entity_id": entry.entity_id},
        )
        await hass.async_block_till_done()

    assert to_update == []
    assert to_remove == [entry.entity_id]

    with patch_sync_helper() as (to_update, to_remove):
        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {
                "action": "update",
                "entity_id": entry.entity_id,
                "changes": ["entity_id"],
                "old_entity_id": "light.living_room",
            },
        )
        await hass.async_block_till_done()

    assert to_update == [entry.entity_id]
    assert to_remove == ["light.living_room"]

    with patch_sync_helper() as (to_update, to_remove):
        hass.bus.async_fire(
            er.EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "update", "entity_id": entry.entity_id, "changes": ["icon"]},
        )
        await hass.async_block_till_done()

    assert to_update == []
    assert to_remove == []