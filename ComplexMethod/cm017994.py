async def test_domains_gets_domains_excludes_ignore_and_disabled(
    manager: config_entries.ConfigEntries,
) -> None:
    """Test we only return each domain once."""
    MockConfigEntry(domain="test").add_to_manager(manager)
    MockConfigEntry(domain="test2").add_to_manager(manager)
    MockConfigEntry(domain="test2").add_to_manager(manager)
    MockConfigEntry(
        domain="ignored", source=config_entries.SOURCE_IGNORE
    ).add_to_manager(manager)
    MockConfigEntry(domain="test3").add_to_manager(manager)
    MockConfigEntry(
        domain="disabled", disabled_by=config_entries.ConfigEntryDisabler.USER
    ).add_to_manager(manager)
    assert manager.async_domains() == ["test", "test2", "test3"]
    assert manager.async_domains(include_ignore=False) == ["test", "test2", "test3"]
    assert manager.async_domains(include_disabled=False) == ["test", "test2", "test3"]
    assert manager.async_domains(include_ignore=False, include_disabled=False) == [
        "test",
        "test2",
        "test3",
    ]

    assert manager.async_domains(include_ignore=True) == [
        "test",
        "test2",
        "ignored",
        "test3",
    ]
    assert manager.async_domains(include_disabled=True) == [
        "test",
        "test2",
        "test3",
        "disabled",
    ]
    assert manager.async_domains(include_ignore=True, include_disabled=True) == [
        "test",
        "test2",
        "ignored",
        "test3",
        "disabled",
    ]