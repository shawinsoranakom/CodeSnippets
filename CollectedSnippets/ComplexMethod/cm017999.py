async def test_updating_subentry_data(
    manager: config_entries.ConfigEntries, freezer: FrozenDateTimeFactory
) -> None:
    """Test that we can update an entry data."""
    created = dt_util.utcnow()
    subentry_id = "blabla"
    entry = MockConfigEntry(
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={"first": True},
                subentry_id=subentry_id,
                subentry_type="test",
                unique_id="unique",
                title="Mock title",
            )
        ]
    )
    subentry = entry.subentries[subentry_id]
    entry.add_to_manager(manager)

    assert len(manager.async_entries()) == 1
    assert manager.async_entries()[0] == entry
    assert entry.created_at == created
    assert entry.modified_at == created

    freezer.tick()

    assert manager.async_update_subentry(entry, subentry) is False
    assert entry.subentries == {
        subentry_id: config_entries.ConfigSubentry(
            data={"first": True},
            subentry_id=subentry_id,
            subentry_type="test",
            title="Mock title",
            unique_id="unique",
        )
    }
    assert entry.modified_at == created
    assert manager.async_entries()[0].modified_at == created

    freezer.tick()
    modified = dt_util.utcnow()

    assert manager.async_update_subentry(entry, subentry, data={"second": True}) is True
    assert entry.subentries == {
        subentry_id: config_entries.ConfigSubentry(
            data={"second": True},
            subentry_id=subentry_id,
            subentry_type="test",
            title="Mock title",
            unique_id="unique",
        )
    }
    assert entry.modified_at == modified
    assert manager.async_entries()[0].modified_at == modified