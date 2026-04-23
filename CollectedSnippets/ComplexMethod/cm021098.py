async def test_settings(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test the P1 Monitor - Settings sensors."""
    entry_id = init_integration.entry_id

    state = hass.states.get("sensor.settings_energy_consumption_price_low")
    entry = entity_registry.async_get("sensor.settings_energy_consumption_price_low")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_settings_energy_consumption_price_low"
    assert state.state == "0.20522"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Settings Energy consumption price - Low"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )

    state = hass.states.get("sensor.settings_energy_production_price_low")
    entry = entity_registry.async_get("sensor.settings_energy_production_price_low")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_settings_energy_production_price_low"
    assert state.state == "0.20522"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Settings Energy production price - Low"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.MEASUREMENT
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, f"{entry_id}_settings")}
    assert device_entry.manufacturer == "P1 Monitor"
    assert device_entry.name == "Settings"
    assert device_entry.entry_type is dr.DeviceEntryType.SERVICE
    assert not device_entry.model
    assert not device_entry.sw_version