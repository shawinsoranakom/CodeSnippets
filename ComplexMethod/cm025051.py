async def test_yaml_collection() -> None:
    """Test a YAML collection."""
    id_manager = collection.IDManager()
    coll = collection.YamlCollection(_LOGGER, id_manager)
    changes = track_changes(coll)
    await coll.async_load(
        [{"id": "mock-1", "name": "Mock 1"}, {"id": "mock-2", "name": "Mock 2"}]
    )
    assert id_manager.has_id("mock-1")
    assert id_manager.has_id("mock-2")
    assert len(changes) == 2
    assert changes[0] == (
        collection.CHANGE_ADDED,
        "mock-1",
        {"id": "mock-1", "name": "Mock 1"},
    )
    assert changes[1] == (
        collection.CHANGE_ADDED,
        "mock-2",
        {"id": "mock-2", "name": "Mock 2"},
    )

    # Test loading new data. Mock 1 is updated, 2 removed, 3 added.
    await coll.async_load(
        [{"id": "mock-1", "name": "Mock 1-updated"}, {"id": "mock-3", "name": "Mock 3"}]
    )
    assert len(changes) == 5
    assert changes[2] == (
        collection.CHANGE_UPDATED,
        "mock-1",
        {"id": "mock-1", "name": "Mock 1-updated"},
    )
    assert changes[3] == (
        collection.CHANGE_ADDED,
        "mock-3",
        {"id": "mock-3", "name": "Mock 3"},
    )
    assert changes[4] == (
        collection.CHANGE_REMOVED,
        "mock-2",
        {"id": "mock-2", "name": "Mock 2"},
    )