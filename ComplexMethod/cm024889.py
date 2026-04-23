async def test_reset_right_after_remove_entity_registry(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test resetting the platform right after removing an entity from the registry.

    A reset commonly happens during a reload.
    """
    result = []

    entry = entity_registry.async_get_or_create(
        "test", "test_platform", "5678", suggested_object_id="test"
    )
    assert entry.entity_id == "test.test"

    class MockEntity(entity.Entity):
        _attr_unique_id = "5678"

        def __init__(self) -> None:
            self.added_calls = []
            self.remove_calls = []

        async def async_added_to_hass(self):
            self.added_calls.append(None)
            self.async_on_remove(lambda: result.append(1))

        async def async_will_remove_from_hass(self):
            self.remove_calls.append(None)

    platform = MockEntityPlatform(hass, domain="test")
    ent = MockEntity()
    await platform.async_add_entities([ent])
    assert hass.states.get("test.test").state == STATE_UNKNOWN
    assert len(ent.added_calls) == 1

    entry = entity_registry.async_remove(entry.entity_id)

    # Reset the platform immediately after removing the entity from the registry
    await platform.async_reset()
    await hass.async_block_till_done()

    assert len(result) == 1
    assert len(ent.added_calls) == 1
    assert len(ent.remove_calls) == 1

    assert hass.states.get("test.test") is None