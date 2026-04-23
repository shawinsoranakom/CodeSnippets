async def test_entries_excludes_ignore_and_disabled(
    manager: config_entries.ConfigEntries,
) -> None:
    """Test ignored and disabled entries are returned by default."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_manager(manager)
    entry2a = MockConfigEntry(domain="test2")
    entry2a.add_to_manager(manager)
    entry2b = MockConfigEntry(domain="test2")
    entry2b.add_to_manager(manager)
    entry_ignored = MockConfigEntry(
        domain="ignored", source=config_entries.SOURCE_IGNORE
    )
    entry_ignored.add_to_manager(manager)
    entry3 = MockConfigEntry(domain="test3")
    entry3.add_to_manager(manager)
    disabled_entry = MockConfigEntry(
        domain="disabled", disabled_by=config_entries.ConfigEntryDisabler.USER
    )
    disabled_entry.add_to_manager(manager)
    assert manager.async_entries() == [
        entry,
        entry2a,
        entry2b,
        entry_ignored,
        entry3,
        disabled_entry,
    ]
    assert manager.async_has_entries("test") is True
    assert manager.async_has_entries("test2") is True
    assert manager.async_has_entries("test3") is True
    assert manager.async_has_entries("ignored") is True
    assert manager.async_has_entries("disabled") is True

    assert manager.async_has_entries("not") is False
    assert manager.async_entries(include_ignore=False) == [
        entry,
        entry2a,
        entry2b,
        entry3,
        disabled_entry,
    ]
    assert manager.async_entries(include_disabled=False) == [
        entry,
        entry2a,
        entry2b,
        entry_ignored,
        entry3,
    ]
    assert manager.async_entries(include_ignore=False, include_disabled=False) == [
        entry,
        entry2a,
        entry2b,
        entry3,
    ]
    assert manager.async_has_entries("test", include_ignore=False) is True
    assert manager.async_has_entries("test2", include_ignore=False) is True
    assert manager.async_has_entries("test3", include_ignore=False) is True
    assert manager.async_has_entries("ignored", include_ignore=False) is False

    assert manager.async_entries(include_ignore=True) == [
        entry,
        entry2a,
        entry2b,
        entry_ignored,
        entry3,
        disabled_entry,
    ]
    assert manager.async_entries(include_disabled=True) == [
        entry,
        entry2a,
        entry2b,
        entry_ignored,
        entry3,
        disabled_entry,
    ]
    assert manager.async_entries(include_ignore=True, include_disabled=True) == [
        entry,
        entry2a,
        entry2b,
        entry_ignored,
        entry3,
        disabled_entry,
    ]
    assert manager.async_has_entries("test", include_disabled=False) is True
    assert manager.async_has_entries("test2", include_disabled=False) is True
    assert manager.async_has_entries("test3", include_disabled=False) is True
    assert manager.async_has_entries("disabled", include_disabled=False) is False