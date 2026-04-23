async def test_name(hass: HomeAssistant, entity_registry: er.EntityRegistry) -> None:
    """Test the config flow name is copied from registry entry, with fallback to state."""
    entity_id = "switch.ceiling"

    # No entry or state, use Object ID
    assert wrapped_entity_config_entry_title(hass, entity_id) == "ceiling"

    # State set, use name from state
    hass.states.async_set(entity_id, "on", {"friendly_name": "State Name"})
    assert wrapped_entity_config_entry_title(hass, entity_id) == "State Name"

    # Entity registered, use original name from registry entry
    hass.states.async_remove(entity_id)
    entry = entity_registry.async_get_or_create(
        "switch",
        "test",
        "unique",
        suggested_object_id="ceiling",
        original_name="Original Name",
    )
    hass.states.async_set(entity_id, "on", {"friendly_name": "State Name"})
    assert entry.entity_id == entity_id
    assert wrapped_entity_config_entry_title(hass, entity_id) == "Original Name"
    assert wrapped_entity_config_entry_title(hass, entry.id) == "Original Name"

    # Entity has customized name
    entity_registry.async_update_entity("switch.ceiling", name="Custom Name")
    assert wrapped_entity_config_entry_title(hass, entity_id) == "Custom Name"
    assert wrapped_entity_config_entry_title(hass, entry.id) == "Custom Name"