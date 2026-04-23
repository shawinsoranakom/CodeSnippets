async def test_update_entity_unique_id(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test entity's unique_id is updated."""
    mock_config = MockConfigEntry(domain="light", entry_id="mock-id-1")
    mock_config.add_to_hass(hass)

    entry = entity_registry.async_get_or_create(
        "light", "hue", "5678", config_entry=mock_config
    )
    assert (
        entity_registry.async_get_entity_id("light", "hue", "5678") == entry.entity_id
    )

    new_unique_id = "1234"
    with patch.object(entity_registry, "async_schedule_save") as mock_schedule_save:
        updated_entry = entity_registry.async_update_entity(
            entry.entity_id, new_unique_id=new_unique_id
        )
    assert updated_entry != entry
    assert updated_entry.unique_id == new_unique_id
    assert updated_entry.previous_unique_id == "5678"
    assert mock_schedule_save.call_count == 1

    assert entity_registry.async_get_entity_id("light", "hue", "5678") is None
    assert (
        entity_registry.async_get_entity_id("light", "hue", "1234") == entry.entity_id
    )