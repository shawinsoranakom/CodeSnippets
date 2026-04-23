async def test_config_parameter_sensor(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    climate_adc_t3000,
    lock_id_lock_as_id150,
    integration,
) -> None:
    """Test config parameter sensor is created."""
    sensor_entity_id = "sensor.adc_t3000_system_configuration_cool_stages"
    sensor_with_states_entity_id = "sensor.adc_t3000_power_source"
    for entity_id in (sensor_entity_id, sensor_with_states_entity_id):
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry
        assert entity_entry.disabled
        assert entity_entry.entity_category == EntityCategory.DIAGNOSTIC

    for entity_id in (sensor_entity_id, sensor_with_states_entity_id):
        updated_entry = entity_registry.async_update_entity(entity_id, disabled_by=None)
        assert updated_entry != entity_entry
        assert updated_entry.disabled is False

    # reload integration and check if entity is correctly there
    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(sensor_entity_id)
    assert state
    assert state.state == "1"

    state = hass.states.get(sensor_with_states_entity_id)
    assert state
    assert state.state == "C-Wire"

    updated_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, disabled_by=None
    )
    assert updated_entry != entity_entry
    assert updated_entry.disabled is False

    # reload integration and check if entity is correctly there
    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()