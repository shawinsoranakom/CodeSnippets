async def test_list_keys(manager: InMemoryRecordManager) -> None:
    """Test listing keys based on the provided date range."""
    # Insert records
    assert manager.list_keys() == []
    assert await manager.alist_keys() == []

    with patch.object(
        manager,
        "get_time",
        return_value=datetime(2021, 1, 2, tzinfo=timezone.utc).timestamp(),
    ):
        manager.update(["key1", "key2"])
        manager.update(["key3"], group_ids=["group1"])
        manager.update(["key4"], group_ids=["group2"])

    with patch.object(
        manager,
        "get_time",
        return_value=datetime(2021, 1, 10, tzinfo=timezone.utc).timestamp(),
    ):
        manager.update(["key5"])

    assert sorted(manager.list_keys()) == ["key1", "key2", "key3", "key4", "key5"]
    assert sorted(await manager.alist_keys()) == [
        "key1",
        "key2",
        "key3",
        "key4",
        "key5",
    ]

    # By group
    assert manager.list_keys(group_ids=["group1"]) == ["key3"]
    assert await manager.alist_keys(group_ids=["group1"]) == ["key3"]

    # Before
    assert sorted(
        manager.list_keys(before=datetime(2021, 1, 3, tzinfo=timezone.utc).timestamp())
    ) == [
        "key1",
        "key2",
        "key3",
        "key4",
    ]
    assert sorted(
        await manager.alist_keys(
            before=datetime(2021, 1, 3, tzinfo=timezone.utc).timestamp()
        )
    ) == [
        "key1",
        "key2",
        "key3",
        "key4",
    ]

    # After
    assert sorted(
        manager.list_keys(after=datetime(2021, 1, 3, tzinfo=timezone.utc).timestamp())
    ) == ["key5"]
    assert sorted(
        await manager.alist_keys(
            after=datetime(2021, 1, 3, tzinfo=timezone.utc).timestamp()
        )
    ) == ["key5"]

    results = manager.list_keys(limit=1)
    assert len(results) == 1
    assert results[0] in {"key1", "key2", "key3", "key4", "key5"}

    results = await manager.alist_keys(limit=1)
    assert len(results) == 1
    assert results[0] in {"key1", "key2", "key3", "key4", "key5"}