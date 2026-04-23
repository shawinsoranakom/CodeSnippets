async def test_updating_entry_system_options(
    manager: config_entries.ConfigEntries, freezer: FrozenDateTimeFactory
) -> None:
    """Test that we can update an entry data."""
    created = dt_util.utcnow()
    entry = MockConfigEntry(
        domain="test",
        data={"first": True},
        state=config_entries.ConfigEntryState.SETUP_ERROR,
        pref_disable_new_entities=True,
    )
    entry.add_to_manager(manager)

    assert entry.pref_disable_new_entities is True
    assert entry.pref_disable_polling is False
    assert entry.created_at == created
    assert entry.modified_at == created

    freezer.tick()
    modified = dt_util.utcnow()

    manager.async_update_entry(
        entry, pref_disable_new_entities=False, pref_disable_polling=True
    )

    assert entry.pref_disable_new_entities is False
    assert entry.pref_disable_polling is True
    assert entry.created_at == created
    assert entry.modified_at == modified