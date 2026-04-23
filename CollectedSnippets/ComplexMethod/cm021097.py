async def test_phases(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test the P1 Monitor - Phases sensors."""
    entry_id = init_integration.entry_id

    state = hass.states.get("sensor.phases_voltage_phase_l1")
    entry = entity_registry.async_get("sensor.phases_voltage_phase_l1")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_phases_voltage_phase_l1"
    assert state.state == "233.6"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Phases Voltage phase L1"
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfElectricPotential.VOLT
    )
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.VOLTAGE

    state = hass.states.get("sensor.phases_current_phase_l1")
    entry = entity_registry.async_get("sensor.phases_current_phase_l1")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_phases_current_phase_l1"
    assert state.state == "1.6"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Phases Current phase L1"
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfElectricCurrent.AMPERE
    )
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.CURRENT

    state = hass.states.get("sensor.phases_power_consumed_phase_l1")
    entry = entity_registry.async_get("sensor.phases_power_consumed_phase_l1")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_phases_power_consumed_phase_l1"
    assert state.state == "315"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Phases Power consumed phase L1"
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, f"{entry_id}_phases")}
    assert device_entry.manufacturer == "P1 Monitor"
    assert device_entry.name == "Phases"
    assert device_entry.entry_type is dr.DeviceEntryType.SERVICE
    assert not device_entry.model
    assert not device_entry.sw_version