async def test_watermeter(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test the P1 Monitor - WaterMeter sensors."""
    entry_id = init_integration.entry_id
    state = hass.states.get("sensor.watermeter_consumption_day")
    entry = entity_registry.async_get("sensor.watermeter_consumption_day")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_watermeter_consumption_day"
    assert state.state == "112.0"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "WaterMeter Consumption day"
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.TOTAL_INCREASING
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfVolume.LITERS

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, f"{entry_id}_watermeter")}
    assert device_entry.manufacturer == "P1 Monitor"
    assert device_entry.name == "WaterMeter"
    assert device_entry.entry_type is dr.DeviceEntryType.SERVICE
    assert not device_entry.model
    assert not device_entry.sw_version