async def test_storage_collection(hass: HomeAssistant) -> None:
    """Test storage collection."""
    store = storage.Store(hass, 1, "test-data")
    await store.async_save(
        {
            "items": [
                {"id": "mock-1", "name": "Mock 1", "data": 1},
                {"id": "mock-2", "name": "Mock 2", "data": 2},
            ]
        }
    )
    id_manager = collection.IDManager()
    coll = MockStorageCollection(store, id_manager)
    changes = track_changes(coll)

    await coll.async_load()
    assert id_manager.has_id("mock-1")
    assert id_manager.has_id("mock-2")
    assert len(changes) == 2
    assert changes[0] == (
        collection.CHANGE_ADDED,
        "mock-1",
        {"id": "mock-1", "name": "Mock 1", "data": 1},
    )
    assert changes[1] == (
        collection.CHANGE_ADDED,
        "mock-2",
        {"id": "mock-2", "name": "Mock 2", "data": 2},
    )

    item = await coll.async_create_item({"name": "Mock 3"})
    assert item["id"] == "mock_3"
    assert len(changes) == 3
    assert changes[2] == (
        collection.CHANGE_ADDED,
        "mock_3",
        {"id": "mock_3", "name": "Mock 3"},
    )

    updated_item = await coll.async_update_item("mock-2", {"name": "Mock 2 updated"})
    assert id_manager.has_id("mock-2")
    assert updated_item == {"id": "mock-2", "name": "Mock 2 updated", "data": 2}
    assert len(changes) == 4
    assert changes[3] == (collection.CHANGE_UPDATED, "mock-2", updated_item)

    with pytest.raises(ValueError):
        await coll.async_update_item("mock-2", {"id": "mock-2-updated"})

    assert id_manager.has_id("mock-2")
    assert not id_manager.has_id("mock-2-updated")
    assert len(changes) == 4

    await flush_store(store)

    assert await storage.Store(hass, 1, "test-data").async_load() == {
        "items": [
            {"id": "mock-1", "name": "Mock 1", "data": 1},
            {"id": "mock-2", "name": "Mock 2 updated", "data": 2},
            {"id": "mock_3", "name": "Mock 3"},
        ]
    }