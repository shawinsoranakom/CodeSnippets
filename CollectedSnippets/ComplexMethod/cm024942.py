async def test_update_entity_entity_id_without_state(
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entity's entity_id is updated for entity without a state."""
    entry = entity_registry.async_get_or_create("light", "hue", "5678")

    assert (
        entity_registry.async_get_entity_id("light", "hue", "5678") == entry.entity_id
    )

    new_entity_id = "light.blah"
    assert new_entity_id != entry.entity_id
    with patch.object(entity_registry, "async_schedule_save") as mock_schedule_save:
        updated_entry = entity_registry.async_update_entity(
            entry.entity_id, new_entity_id=new_entity_id
        )
    assert updated_entry != entry
    assert updated_entry.entity_id == new_entity_id
    assert mock_schedule_save.call_count == 1

    assert entity_registry.async_get(entry.entity_id) is None
    assert entity_registry.async_get(new_entity_id) is not None