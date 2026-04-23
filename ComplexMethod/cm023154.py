async def test_shelly_001p10_disabled_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    shelly_qnsh_001P10_shutter,
    integration,
) -> None:
    """Test that Shelly 001P10 entity created by endpoint 2 is disabled."""
    entity_ids = [
        "cover.wave_shutter_2",
    ]
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state is None
        entry = entity_registry.async_get(entity_id)
        assert entry
        assert entry.disabled
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

        # Test enabling entity
        updated_entry = entity_registry.async_update_entity(
            entry.entity_id, disabled_by=None
        )
        assert updated_entry != entry
        assert updated_entry.disabled is False

    # Test if the main entity from endpoint 1 was created.
    state = hass.states.get("cover.wave_shutter")
    assert state