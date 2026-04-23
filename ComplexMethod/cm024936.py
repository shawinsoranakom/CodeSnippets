async def test_deleted_entity_removing_config_entry_id(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that we update config entry id in registry on deleted entity."""
    mock_config1 = MockConfigEntry(domain="light", entry_id="mock-id-1")
    mock_config2 = MockConfigEntry(domain="light", entry_id="mock-id-2")
    mock_config1.add_to_hass(hass)
    mock_config2.add_to_hass(hass)

    entry1 = entity_registry.async_get_or_create(
        "light", "hue", "5678", config_entry=mock_config1
    )
    assert entry1.config_entry_id == "mock-id-1"
    entry2 = entity_registry.async_get_or_create(
        "light", "hue", "1234", config_entry=mock_config2
    )
    assert entry2.config_entry_id == "mock-id-2"
    entity_registry.async_remove(entry1.entity_id)
    entity_registry.async_remove(entry2.entity_id)

    assert len(entity_registry.entities) == 0
    assert len(entity_registry.deleted_entities) == 2
    deleted_entry1 = entity_registry.deleted_entities[("light", "hue", "5678")]
    assert deleted_entry1.config_entry_id == "mock-id-1"
    assert deleted_entry1.orphaned_timestamp is None
    deleted_entry2 = entity_registry.deleted_entities[("light", "hue", "1234")]
    assert deleted_entry2.config_entry_id == "mock-id-2"
    assert deleted_entry2.orphaned_timestamp is None

    entity_registry.async_clear_config_entry("mock-id-1")
    assert len(entity_registry.entities) == 0
    assert len(entity_registry.deleted_entities) == 2
    deleted_entry1 = entity_registry.deleted_entities[("light", "hue", "5678")]
    assert deleted_entry1.config_entry_id is None
    assert deleted_entry1.orphaned_timestamp is not None
    assert entity_registry.deleted_entities[("light", "hue", "1234")] == deleted_entry2