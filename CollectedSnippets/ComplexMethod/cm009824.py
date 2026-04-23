def test_update_timestamp(manager: InMemoryRecordManager) -> None:
    """Test updating records in the database."""
    # no keys should be present in the set
    with patch.object(
        manager,
        "get_time",
        return_value=datetime(2021, 1, 2, tzinfo=timezone.utc).timestamp(),
    ):
        manager.update(["key1"])

    assert manager.list_keys() == ["key1"]
    assert (
        manager.list_keys(before=datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
        == []
    )
    assert manager.list_keys(
        after=datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
    ) == ["key1"]
    assert (
        manager.list_keys(after=datetime(2021, 1, 3, tzinfo=timezone.utc).timestamp())
        == []
    )

    # Update the timestamp
    with patch.object(
        manager,
        "get_time",
        return_value=datetime(2023, 1, 5, tzinfo=timezone.utc).timestamp(),
    ):
        manager.update(["key1"])

    assert manager.list_keys() == ["key1"]
    assert (
        manager.list_keys(before=datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
        == []
    )
    assert manager.list_keys(
        after=datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp()
    ) == ["key1"]
    assert manager.list_keys(
        after=datetime(2023, 1, 3, tzinfo=timezone.utc).timestamp()
    ) == ["key1"]