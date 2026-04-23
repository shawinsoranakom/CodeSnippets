async def test_config_parameter_select(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    climate_adc_t3000,
    integration,
) -> None:
    """Test config parameter select is created."""
    select_entity_id = "select.adc_t3000_hvac_system_type"
    entity_entry = entity_registry.async_get(select_entity_id)
    assert entity_entry
    assert entity_entry.disabled
    assert entity_entry.entity_category == EntityCategory.CONFIG

    updated_entry = entity_registry.async_update_entity(
        select_entity_id, disabled_by=None
    )
    assert updated_entry != entity_entry
    assert updated_entry.disabled is False

    # reload integration and check if entity is correctly there
    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(select_entity_id)
    assert state
    assert state.state == "Normal"