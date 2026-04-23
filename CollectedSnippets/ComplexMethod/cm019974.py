async def test_gas_today(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test the easyEnergy - Gas sensors."""
    entry_id = init_integration.entry_id

    # Current gas price sensor
    state = hass.states.get("sensor.easyenergy_today_gas_current_hour_price")
    entry = entity_registry.async_get("sensor.easyenergy_today_gas_current_hour_price")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_gas_current_hour_price"
    assert state.state == "0.7253"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Gas market price Current hour"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfVolume.CUBIC_METERS}"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, f"{entry_id}_today_gas")}
    assert device_entry.manufacturer == "easyEnergy"
    assert device_entry.name == "Gas market price"
    assert device_entry.entry_type is dr.DeviceEntryType.SERVICE
    assert not device_entry.model
    assert not device_entry.sw_version