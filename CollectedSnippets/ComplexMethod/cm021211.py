async def test_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test the Forecast.Solar sensors."""
    entry_id = init_integration.entry_id

    state = hass.states.get("sensor.energy_production_today")
    entry = entity_registry.async_get("sensor.energy_production_today")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_energy_production_today"
    assert state.state == "100.0"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Solar production forecast Estimated energy production - today"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert ATTR_ICON not in state.attributes

    state = hass.states.get("sensor.energy_production_today_remaining")
    entry = entity_registry.async_get("sensor.energy_production_today_remaining")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_energy_production_today_remaining"
    assert state.state == "50.0"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Solar production forecast Estimated energy production - remaining today"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert ATTR_ICON not in state.attributes

    state = hass.states.get("sensor.energy_production_tomorrow")
    entry = entity_registry.async_get("sensor.energy_production_tomorrow")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_energy_production_tomorrow"
    assert state.state == "200.0"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Solar production forecast Estimated energy production - tomorrow"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert ATTR_ICON not in state.attributes

    state = hass.states.get("sensor.power_highest_peak_time_today")
    entry = entity_registry.async_get("sensor.power_highest_peak_time_today")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_power_highest_peak_time_today"
    assert state.state == "2021-06-27T20:00:00+00:00"  # Timestamp sensor is UTC
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Solar production forecast Highest power peak time - today"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TIMESTAMP
    assert ATTR_UNIT_OF_MEASUREMENT not in state.attributes
    assert ATTR_ICON not in state.attributes

    state = hass.states.get("sensor.power_highest_peak_time_tomorrow")
    entry = entity_registry.async_get("sensor.power_highest_peak_time_tomorrow")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_power_highest_peak_time_tomorrow"
    assert state.state == "2021-06-27T21:00:00+00:00"  # Timestamp sensor is UTC
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Solar production forecast Highest power peak time - tomorrow"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TIMESTAMP
    assert ATTR_UNIT_OF_MEASUREMENT not in state.attributes
    assert ATTR_ICON not in state.attributes

    state = hass.states.get("sensor.power_production_now")
    entry = entity_registry.async_get("sensor.power_production_now")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_power_production_now"
    assert state.state == "300000"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Solar production forecast Estimated power production - now"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER
    assert ATTR_ICON not in state.attributes

    state = hass.states.get("sensor.energy_current_hour")
    entry = entity_registry.async_get("sensor.energy_current_hour")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_energy_current_hour"
    assert state.state == "800.0"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Solar production forecast Estimated energy production - this hour"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert ATTR_ICON not in state.attributes

    state = hass.states.get("sensor.energy_next_hour")
    entry = entity_registry.async_get("sensor.energy_next_hour")
    assert entry
    assert state
    assert entry.unique_id == f"{entry_id}_energy_next_hour"
    assert state.state == "900.0"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == "Solar production forecast Estimated energy production - next hour"
    )
    assert state.attributes.get(ATTR_STATE_CLASS) is None
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENERGY
    assert ATTR_ICON not in state.attributes

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.identifiers == {(DOMAIN, f"{entry_id}")}
    assert device_entry.manufacturer == "Forecast.Solar"
    assert device_entry.name == "Solar production forecast"
    assert device_entry.entry_type is dr.DeviceEntryType.SERVICE
    assert device_entry.model == "public"
    assert not device_entry.sw_version