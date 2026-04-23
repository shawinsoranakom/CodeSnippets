async def test_loading_old_data(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test automatically migrating old data."""
    hass_storage[config_entries.STORAGE_KEY] = {
        "version": 1,
        "data": {
            "entries": [
                {
                    "version": 5,
                    "domain": "my_domain",
                    "entry_id": "mock-id",
                    "data": {"my": "data"},
                    "source": "user",
                    "title": "Mock title",
                    "system_options": {"disable_new_entities": True},
                }
            ]
        },
    }
    manager = config_entries.ConfigEntries(hass, {})
    await manager.async_initialize()

    entries = manager.async_entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.version == 5
    assert entry.domain == "my_domain"
    assert entry.entry_id == "mock-id"
    assert entry.title == "Mock title"
    assert entry.data == {"my": "data"}
    assert entry.pref_disable_new_entities is True