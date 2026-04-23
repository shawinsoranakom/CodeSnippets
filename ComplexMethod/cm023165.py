async def test_battery_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    ring_keypad: Node,
    integration: MockConfigEntry,
) -> None:
    """Test boolean battery binary sensors."""
    entity_id = "binary_sensor.keypad_v2_low_battery_level"
    state = hass.states.get(entity_id)

    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.BATTERY

    entity_entry = entity_registry.async_get(entity_id)

    assert entity_entry
    assert entity_entry.entity_category is EntityCategory.DIAGNOSTIC

    disabled_binary_sensor_battery_entities = (
        "binary_sensor.keypad_v2_battery_is_disconnected",
        "binary_sensor.keypad_v2_fluid_is_low",
        "binary_sensor.keypad_v2_overheating",
        "binary_sensor.keypad_v2_rechargeable",
        "binary_sensor.keypad_v2_used_as_backup",
    )

    for entity_id in disabled_binary_sensor_battery_entities:
        state = hass.states.get(entity_id)
        assert state is None  # disabled by default

        entity_entry = entity_registry.async_get(entity_id)

        assert entity_entry
        assert entity_entry.entity_category is EntityCategory.DIAGNOSTIC
        assert entity_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

        entity_registry.async_update_entity(entity_id, disabled_by=None)

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    for entity_id in disabled_binary_sensor_battery_entities:
        state = hass.states.get(entity_id)
        assert state
        assert state.state == STATE_OFF