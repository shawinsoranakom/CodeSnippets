async def test_battery_attributes(
    hass: HomeAssistant, async_autosetup_sonos, soco, entity_registry: er.EntityRegistry
) -> None:
    """Test sonos device with battery state."""
    battery = entity_registry.entities["sensor.zone_a_battery"]
    battery_state = hass.states.get(battery.entity_id)
    assert battery_state.state == "100"
    assert battery_state.attributes.get("unit_of_measurement") == "%"

    power = entity_registry.entities["binary_sensor.zone_a_charging"]
    power_state = hass.states.get(power.entity_id)
    assert power_state.state == STATE_ON
    assert (
        power_state.attributes.get(ATTR_BATTERY_POWER_SOURCE) == "SONOS_CHARGING_RING"
    )

    power_source = entity_registry.entities["sensor.zone_a_power_source"]
    power_source_state = hass.states.get(power_source.entity_id)
    assert power_source_state.state == HA_POWER_SOURCE_CHARGING_BASE
    assert power_source_state.attributes.get("device_class") == SensorDeviceClass.ENUM
    assert power_source_state.attributes.get("options") == [
        HA_POWER_SOURCE_BATTERY,
        HA_POWER_SOURCE_CHARGING_BASE,
        HA_POWER_SOURCE_USB,
    ]
    result = translation.async_translate_state(
        hass,
        power_source_state.state,
        Platform.SENSOR,
        DOMAIN,
        power_source.translation_key,
        None,
    )
    assert result == "Charging base"