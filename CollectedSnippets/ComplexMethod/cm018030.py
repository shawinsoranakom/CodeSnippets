async def test_async_update_entry_unique_id_collision(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    caplog: pytest.LogCaptureFixture,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test we warn when async_update_entry creates a unique_id collision.

    Also test an issue registry issue is created.
    """
    assert len(issue_registry.issues) == 0

    entry1 = MockConfigEntry(domain="test", unique_id=None)
    entry2 = MockConfigEntry(domain="test", unique_id="not none")
    entry3 = MockConfigEntry(domain="test", unique_id="very unique")
    entry4 = MockConfigEntry(domain="test", unique_id="also very unique")
    entry1.add_to_manager(manager)
    entry2.add_to_manager(manager)
    entry3.add_to_manager(manager)
    entry4.add_to_manager(manager)

    manager.async_update_entry(entry2, unique_id=None)
    assert len(issue_registry.issues) == 0
    assert len(caplog.record_tuples) == 0

    manager.async_update_entry(entry4, unique_id="very unique")
    assert len(issue_registry.issues) == 1
    assert len(caplog.record_tuples) == 1

    assert (
        "Unique id of config entry 'Mock Title' from integration test changed to "
        "'very unique' which is already in use"
    ) in caplog.text

    issue_id = "config_entry_unique_id_collision_test_very unique"
    assert issue_registry.async_get_issue(HOMEASSISTANT_DOMAIN, issue_id)