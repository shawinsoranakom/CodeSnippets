async def test_entity_component_collection_entity_removed(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test entity removal is handled."""
    ent_comp = entity_component.EntityComponent(_LOGGER, "test", hass)
    await ent_comp.async_setup({})
    coll = MockObservableCollection(None)

    async_update_config_calls = []
    async_remove_calls = []

    class MockMockEntity(MockEntity):
        """Track calls to async_update_config and async_remove."""

        async def async_update_config(self, config):
            nonlocal async_update_config_calls
            async_update_config_calls.append(None)
            await super().async_update_config()

        async def async_remove(self, *, force_remove: bool = False):
            nonlocal async_remove_calls
            async_remove_calls.append(None)
            await super().async_remove()

    collection.sync_entity_lifecycle(
        hass, "test", "test", ent_comp, coll, MockMockEntity
    )
    entity_registry.async_get_or_create(
        "test", "test", "mock_id", suggested_object_id="mock_1"
    )

    await coll.notify_changes(
        [
            collection.CollectionChange(
                collection.CHANGE_ADDED,
                "mock_id",
                {"id": "mock_id", "state": "initial", "name": "Mock 1"},
            )
        ],
    )

    assert hass.states.get("test.mock_1").name == "Mock 1"
    assert hass.states.get("test.mock_1").state == "initial"

    entity_registry.async_remove("test.mock_1")
    await hass.async_block_till_done()
    assert hass.states.get("test.mock_1") is None
    assert len(async_remove_calls) == 1

    await coll.notify_changes(
        [
            collection.CollectionChange(
                collection.CHANGE_UPDATED,
                "mock_id",
                {"id": "mock_id", "state": "second", "name": "Mock 1 updated"},
            )
        ],
    )

    assert hass.states.get("test.mock_1") is None
    assert len(async_update_config_calls) == 0

    await coll.notify_changes(
        [collection.CollectionChange(collection.CHANGE_REMOVED, "mock_id", None)],
    )

    assert hass.states.get("test.mock_1") is None
    assert len(async_remove_calls) == 1