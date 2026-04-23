async def test_update_entity_entity_id_entity_id(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test update raises when entity_id already in use."""
    entry = entity_registry.async_get_or_create("light", "hue", "5678")
    entry2 = entity_registry.async_get_or_create("light", "hue", "1234")
    state_entity_id = "light.blah"
    hass.states.async_set(state_entity_id, "on")
    assert entry.entity_id != state_entity_id
    assert entry2.entity_id != state_entity_id

    # Try updating to a registered entity_id
    with (
        patch.object(entity_registry, "async_schedule_save") as mock_schedule_save,
        pytest.raises(ValueError),
    ):
        entity_registry.async_update_entity(
            entry.entity_id, new_entity_id=entry2.entity_id
        )
    assert mock_schedule_save.call_count == 0
    assert (
        entity_registry.async_get_entity_id("light", "hue", "5678") == entry.entity_id
    )
    assert entity_registry.async_get(entry.entity_id) is entry
    assert (
        entity_registry.async_get_entity_id("light", "hue", "1234") == entry2.entity_id
    )
    assert entity_registry.async_get(entry2.entity_id) is entry2

    # Try updating to an entity_id which is in the state machine
    with (
        patch.object(entity_registry, "async_schedule_save") as mock_schedule_save,
        pytest.raises(ValueError),
    ):
        entity_registry.async_update_entity(
            entry.entity_id, new_entity_id=state_entity_id
        )
    assert mock_schedule_save.call_count == 0
    assert (
        entity_registry.async_get_entity_id("light", "hue", "5678") == entry.entity_id
    )
    assert entity_registry.async_get(entry.entity_id) is entry
    assert entity_registry.async_get(state_entity_id) is None