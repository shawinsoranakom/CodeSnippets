async def test_smartmeter(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test the P1 Monitor - SmartMeter sensors."""
    entry_id = init_integration.entry_id

    state = hass.states.get("sensor.smartmeter_power_consumption")
    entry = entity_registry.async_get("sensor.smartmeter_power_consumption")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_smartmeter_power_consumption"
    assert state.state == "877"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "SmartMeter Power consumption"
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER

    state = hass.states.get("sensor.smartmeter_energy_consumption_high_tariff")
    entry = entity_registry.async_get(
        "sensor.smartmeter_energy_consumption_high_tariff"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_smartmeter_energy_consumption_high"
    assert state.state == "2770.133"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "SmartMeter Energy consumption - High tariff"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.TOTAL_INCREASING
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY

    state = hass.states.get("sensor.smartmeter_energy_tariff_period")
    entry = entity_registry.async_get("sensor.smartmeter_energy_tariff_period")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_smartmeter_energy_tariff_period"
    assert state.state == "high"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "SmartMeter Energy tariff period"
    assert ATTR_UNIT_OF_MEASUREMENT not in state.attributes
    assert ATTR_DEVICE_CLASS not in state.attributes

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, f"{entry_id}_smartmeter")}
    assert device_entry.manufacturer == "P1 Monitor"
    assert device_entry.name == "SmartMeter"
    assert device_entry.entry_type is dr.DeviceEntryType.SERVICE
    assert not device_entry.model
    assert not device_entry.sw_version