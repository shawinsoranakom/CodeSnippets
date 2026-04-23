async def test_battery_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    ring_keypad: Node,
    integration: MockConfigEntry,
) -> None:
    """Test numeric battery sensors."""
    entity_id = "sensor.keypad_v2_battery_level"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "100.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.BATTERY
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry
    assert entity_entry.entity_category is EntityCategory.DIAGNOSTIC

    disabled_sensor_battery_entities = (
        "sensor.keypad_v2_chargingstatus",
        "sensor.keypad_v2_maximum_capacity",
        "sensor.keypad_v2_rechargeorreplace",
        "sensor.keypad_v2_temperature",
    )

    for entity_id in disabled_sensor_battery_entities:
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

    entity_id = "sensor.keypad_v2_chargingstatus"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "Maintaining"
    assert ATTR_UNIT_OF_MEASUREMENT not in state.attributes
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENUM
    assert ATTR_STATE_CLASS not in state.attributes

    entity_id = "sensor.keypad_v2_maximum_capacity"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    entity_id = "sensor.keypad_v2_rechargeorreplace"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "No"
    assert ATTR_UNIT_OF_MEASUREMENT not in state.attributes
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENUM
    assert ATTR_STATE_CLASS not in state.attributes

    entity_id = "sensor.keypad_v2_temperature"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT