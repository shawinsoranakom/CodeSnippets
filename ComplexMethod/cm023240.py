async def test_config_parameter_number(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    climate_adc_t3000,
    integration,
) -> None:
    """Test config parameter number is created."""
    number_entity_id = "number.adc_t3000_heat_staging_delay"
    number_with_states_entity_id = "number.adc_t3000_calibration_temperature"
    for entity_id in (number_entity_id, number_with_states_entity_id):
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry
        assert entity_entry.disabled
        assert entity_entry.entity_category == EntityCategory.CONFIG

    for entity_id in (number_entity_id, number_with_states_entity_id):
        updated_entry = entity_registry.async_update_entity(entity_id, disabled_by=None)
        assert updated_entry != entity_entry
        assert updated_entry.disabled is False

    # reload integration and check if entity is correctly there
    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(number_entity_id)
    assert state
    assert state.state == "30.0"
    assert "reserved_values" not in state.attributes

    state = hass.states.get(number_with_states_entity_id)
    assert state
    assert state.state == "0.0"
    assert "reserved_values" in state.attributes
    assert state.attributes["reserved_values"] == {-1: "Disabled"}