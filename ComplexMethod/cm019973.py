async def test_energy_return_today(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test the easyEnergy - Energy return sensors."""
    entry_id = init_integration.entry_id

    # Current return energy price sensor
    state = hass.states.get("sensor.easyenergy_today_energy_return_current_hour_price")
    entry = entity_registry.async_get(
        "sensor.easyenergy_today_energy_return_current_hour_price"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_return_current_hour_price"
    assert state.state == "0.18629"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Current hour"
    )
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    # Average return energy price sensor
    state = hass.states.get("sensor.easyenergy_today_energy_return_average_price")
    entry = entity_registry.async_get(
        "sensor.easyenergy_today_energy_return_average_price"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_return_average_price"
    assert state.state == "0.14599"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Average - today"
    )
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    # Highest return energy price sensor
    state = hass.states.get("sensor.easyenergy_today_energy_return_max_price")
    entry = entity_registry.async_get("sensor.easyenergy_today_energy_return_max_price")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_return_max_price"
    assert state.state == "0.20394"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Highest price - today"
    )
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_ICON not in state.attributes

    # Highest return price time sensor
    state = hass.states.get("sensor.easyenergy_today_energy_return_highest_price_time")
    entry = entity_registry.async_get(
        "sensor.easyenergy_today_energy_return_highest_price_time"
    )
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_today_energy_return_highest_price_time"
    assert state.state == "2023-01-19T16:00:00+00:00"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Time of highest price - today"
    )
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TIMESTAMP
    assert ATTR_ICON not in state.attributes

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, f"{entry_id}_today_energy_return")}
    assert device_entry.manufacturer == "easyEnergy"
    assert device_entry.name == "Energy market price - Return"
    assert device_entry.entry_type is dr.DeviceEntryType.SERVICE
    assert not device_entry.model
    assert not device_entry.sw_version

    # Return hours priced equal or higher sensor
    state = hass.states.get(
        "sensor.easyenergy_today_energy_return_hours_priced_equal_or_higher"
    )
    entry = entity_registry.async_get(
        "sensor.easyenergy_today_energy_return_hours_priced_equal_or_higher"
    )
    assert entry
    assert state
    assert (
        entry.unique_id
        == f"{entry_id}_today_energy_return_hours_priced_equal_or_higher"
    )
    assert state.state == "3"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Energy market price - Return Hours priced equal or higher than current - today"
    )
    assert ATTR_DEVICE_CLASS not in state.attributes