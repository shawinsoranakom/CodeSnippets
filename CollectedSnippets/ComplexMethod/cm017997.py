async def test_updating_entry_data(
    manager: config_entries.ConfigEntries, freezer: FrozenDateTimeFactory
) -> None:
    """Test that we can update an entry data."""
    created = dt_util.utcnow()
    entry = MockConfigEntry(
        domain="test",
        data={"first": True},
        state=config_entries.ConfigEntryState.SETUP_ERROR,
    )
    entry.add_to_manager(manager)

    assert len(manager.async_entries()) == 1
    assert manager.async_entries()[0] == entry
    assert entry.created_at == created
    assert entry.modified_at == created

    freezer.tick()

    assert manager.async_update_entry(entry) is False
    assert entry.data == {"first": True}
    assert entry.modified_at == created
    assert manager.async_entries()[0].modified_at == created

    freezer.tick()
    modified = dt_util.utcnow()

    assert manager.async_update_entry(entry, data={"second": True}) is True
    assert entry.data == {"second": True}
    assert entry.modified_at == modified
    assert manager.async_entries()[0].modified_at == modified