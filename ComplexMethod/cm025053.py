async def test_storage_collection_update_modifiet_at(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that updating a storage collection will update the modified_at datetime in the entity registry."""

    entities: dict[str, TestEntity] = {}

    class TestEntity(MockEntity):
        """Entity that is config based."""

        def __init__(self, config: ConfigType) -> None:
            """Initialize entity."""
            super().__init__(config)
            self._state = "initial"

        @classmethod
        def from_storage(cls, config: ConfigType) -> TestEntity:
            """Create instance from storage."""
            obj = super().from_storage(config)
            entities[obj.unique_id] = obj
            return obj

        @property
        def state(self) -> str:
            """Return state of entity."""
            return self._state

        def set_state(self, value: str) -> None:
            """Set value."""
            self._state = value
            self.async_write_ha_state()

    store = storage.Store(hass, 1, "test-data")
    data = {"id": "mock-1", "name": "Mock 1", "data": 1}
    await store.async_save(
        {
            "items": [
                data,
            ]
        }
    )
    id_manager = collection.IDManager()
    ent_comp = entity_component.EntityComponent(_LOGGER, "test", hass)
    await ent_comp.async_setup({})
    coll = MockStorageCollection(store, id_manager)
    collection.sync_entity_lifecycle(hass, "test", "test", ent_comp, coll, TestEntity)
    changes = track_changes(coll)

    await coll.async_load()
    assert id_manager.has_id("mock-1")
    assert len(changes) == 1
    assert changes[0] == (collection.CHANGE_ADDED, "mock-1", data)

    modified_1 = entity_registry.async_get("test.mock_1").modified_at
    assert modified_1 == utcnow()

    freezer.tick(timedelta(minutes=1))

    updated_item = await coll.async_update_item("mock-1", {"data": 2})
    assert id_manager.has_id("mock-1")
    assert updated_item == {"id": "mock-1", "name": "Mock 1", "data": 2}
    assert len(changes) == 2
    assert changes[1] == (collection.CHANGE_UPDATED, "mock-1", updated_item)

    modified_2 = entity_registry.async_get("test.mock_1").modified_at
    assert modified_2 > modified_1
    assert modified_2 == utcnow()

    freezer.tick(timedelta(minutes=1))

    entities["mock-1"].set_state("second")

    modified_3 = entity_registry.async_get("test.mock_1").modified_at
    assert modified_3 == modified_2