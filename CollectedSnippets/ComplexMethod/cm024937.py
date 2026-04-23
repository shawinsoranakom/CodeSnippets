async def test_deleted_entity_removing_config_subentry_id(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that we update config subentry id in registry on deleted entity."""
    mock_config = MockConfigEntry(
        domain="light",
        entry_id="mock-id-1",
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-2",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        ],
    )
    mock_config.add_to_hass(hass)

    entry1 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=mock_config,
        config_subentry_id="mock-subentry-id-1",
    )
    assert entry1.config_subentry_id == "mock-subentry-id-1"
    entry2 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "1234",
        config_entry=mock_config,
        config_subentry_id="mock-subentry-id-2",
    )
    assert entry2.config_subentry_id == "mock-subentry-id-2"
    entity_registry.async_remove(entry1.entity_id)
    entity_registry.async_remove(entry2.entity_id)

    assert len(entity_registry.entities) == 0
    assert len(entity_registry.deleted_entities) == 2
    deleted_entry1 = entity_registry.deleted_entities[("light", "hue", "5678")]
    assert deleted_entry1.config_entry_id == "mock-id-1"
    assert deleted_entry1.config_subentry_id == "mock-subentry-id-1"
    assert deleted_entry1.orphaned_timestamp is None
    deleted_entry2 = entity_registry.deleted_entities[("light", "hue", "1234")]
    assert deleted_entry2.config_entry_id == "mock-id-1"
    assert deleted_entry2.config_subentry_id == "mock-subentry-id-2"
    assert deleted_entry2.orphaned_timestamp is None

    hass.config_entries.async_remove_subentry(mock_config, "mock-subentry-id-1")
    assert len(entity_registry.entities) == 0
    assert len(entity_registry.deleted_entities) == 2
    deleted_entry1 = entity_registry.deleted_entities[("light", "hue", "5678")]
    assert deleted_entry1.config_entry_id is None
    assert deleted_entry1.config_subentry_id is None
    assert deleted_entry1.orphaned_timestamp is not None
    assert entity_registry.deleted_entities[("light", "hue", "1234")] == deleted_entry2