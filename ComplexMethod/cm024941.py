async def test_update_entity_entity_id(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test entity's entity_id is updated for entity with a restored state."""
    hass.set_state(CoreState.not_running)

    mock_config = MockConfigEntry(domain="light", entry_id="mock-id-1")
    mock_config.add_to_hass(hass)
    entry = entity_registry.async_get_or_create(
        "light", "hue", "5678", config_entry=mock_config
    )
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START, {})
    await hass.async_block_till_done()
    assert (
        entity_registry.async_get_entity_id("light", "hue", "5678") == entry.entity_id
    )
    state = hass.states.get(entry.entity_id)
    assert state is not None
    assert state.state == "unavailable"
    assert state.attributes == {"restored": True, "supported_features": 0}

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

    # The restored state should be removed
    old_state = hass.states.get(entry.entity_id)
    assert old_state is None

    # The new entity should have an unavailable initial state
    new_state = hass.states.get(new_entity_id)
    assert new_state is not None
    assert new_state.state == "unavailable"