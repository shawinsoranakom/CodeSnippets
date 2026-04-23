async def test_merten_507801_disabled_enitites(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client,
    merten_507801,
    integration,
) -> None:
    """Test that Merten 507801 entities created by endpoint 2 are disabled."""
    entity_ids = [
        "cover.connect_roller_shutter_2",
        "select.connect_roller_shutter_local_protection_state_2",
        "select.connect_roller_shutter_rf_protection_state_2",
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