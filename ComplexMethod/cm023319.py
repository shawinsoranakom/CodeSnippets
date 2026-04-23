async def test_thermostat_fan_without_off(
    hass: HomeAssistant,
    client,
    climate_radio_thermostat_ct100_plus,
    integration,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the fan entity for a z-wave fan without "off" property."""
    entity_id = "fan.z_wave_thermostat"

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

    client.async_send_command.reset_mock()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN

    # Test turning off
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    assert len(client.async_send_command.call_args_list) == 0
    assert state.state == STATE_UNKNOWN

    client.async_send_command.reset_mock()

    # Test turning on
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    assert len(client.async_send_command.call_args_list) == 0
    assert state.state == STATE_UNKNOWN

    client.async_send_command.reset_mock()