async def test_energy_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hank_binary_switch,
    integration,
) -> None:
    """Test power and energy sensors."""
    state = hass.states.get(POWER_SENSOR)

    assert state
    assert state.state == "0.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfPower.WATT
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.POWER
    assert state.attributes[ATTR_STATE_CLASS] is SensorStateClass.MEASUREMENT

    state = hass.states.get(ENERGY_SENSOR)

    assert state
    assert state.state == "0.164"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENERGY
    assert state.attributes[ATTR_STATE_CLASS] is SensorStateClass.TOTAL_INCREASING

    state = hass.states.get(VOLTAGE_SENSOR)

    assert state
    assert state.state == "122.963"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfElectricPotential.VOLT
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.VOLTAGE

    entity_entry = entity_registry.async_get(VOLTAGE_SENSOR)

    assert entity_entry is not None
    sensor_options = entity_entry.options.get("sensor")
    assert sensor_options is not None
    assert sensor_options["suggested_display_precision"] == 0

    state = hass.states.get(CURRENT_SENSOR)

    assert state
    assert state.state == "0.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfElectricCurrent.AMPERE
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.CURRENT