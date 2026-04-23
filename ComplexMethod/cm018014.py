async def test_updating_entry_with_and_without_changes(
    manager: config_entries.ConfigEntries,
) -> None:
    """Test that we can update an entry data."""
    entry = MockConfigEntry(
        domain="test",
        data={"first": True},
        title="thetitle",
        options={"option": True},
        unique_id="abc123",
        state=config_entries.ConfigEntryState.SETUP_ERROR,
    )
    entry.add_to_manager(manager)
    assert "abc123" in str(entry)

    assert manager.async_entry_for_domain_unique_id("test", "abc123") is entry

    assert manager.async_update_entry(entry) is False

    for change, expected_value in (
        ({"data": {"second": True, "third": 456}}, {"second": True, "third": 456}),
        ({"data": {"second": True}}, {"second": True}),
        ({"minor_version": 2}, 2),
        ({"options": {"hello": True}}, {"hello": True}),
        ({"pref_disable_new_entities": True}, True),
        ({"pref_disable_polling": True}, True),
        ({"title": "sometitle"}, "sometitle"),
        ({"unique_id": "abcd1234"}, "abcd1234"),
        ({"version": 2}, 2),
    ):
        assert manager.async_update_entry(entry, **change) is True
        key = next(iter(change))
        assert getattr(entry, key) == expected_value
        assert manager.async_update_entry(entry, **change) is False

    assert manager.async_entry_for_domain_unique_id("test", "abc123") is None
    assert manager.async_entry_for_domain_unique_id("test", "abcd1234") is entry
    assert "abcd1234" in str(entry)