async def test_thermostat_fan_without_preset_modes(
    hass: HomeAssistant,
    client,
    climate_adc_t3000_missing_fan_mode_states,
    integration,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the fan entity for a z-wave fan without "states" metadata."""
    entity_id = "fan.adc_t3000_missing_fan_mode_states"

    state = hass.states.get(entity_id)
    assert state is None

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.disabled
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    # Test enabling entity
    updated_entry = entity_registry.async_update_entity(entity_id, disabled_by=None)
    assert updated_entry != entry
    assert updated_entry.disabled is False

    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state

    assert not state.attributes.get(ATTR_PRESET_MODE)
    assert not state.attributes.get(ATTR_PRESET_MODES)