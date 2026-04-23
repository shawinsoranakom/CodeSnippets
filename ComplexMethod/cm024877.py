async def test_reuse_entity_object_after_entity_registry_remove(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test reuse entity object."""
    entry = entity_registry.async_get_or_create("test", "test", "5678")
    platform = MockEntityPlatform(hass, domain="test", platform_name="test")
    ent = entity.Entity()
    ent._attr_unique_id = "5678"
    assert ent._platform_state == entity.EntityPlatformState.NOT_ADDED
    await platform.async_add_entities([ent])
    assert ent.registry_entry is entry
    assert len(hass.states.async_entity_ids()) == 1
    assert ent._platform_state == entity.EntityPlatformState.ADDED

    entity_registry.async_remove(entry.entity_id)
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids()) == 0
    assert ent._platform_state == entity.EntityPlatformState.REMOVED

    await platform.async_add_entities([ent])
    assert "Entity 'test.test_5678' cannot be added a second time" in caplog.text
    assert len(hass.states.async_entity_ids()) == 0
    assert ent._platform_state == entity.EntityPlatformState.REMOVED