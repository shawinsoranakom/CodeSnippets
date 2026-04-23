async def test_sensors(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Test Flo by Moen sensors."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # we should have 5 entities for the valve
    assert (
        hass.states.get("sensor.smart_water_shutoff_current_system_mode").state
        == "home"
    )

    assert (
        hass.states.get("sensor.smart_water_shutoff_today_s_water_usage").state == "3.7"
    )
    assert (
        hass.states.get("sensor.smart_water_shutoff_today_s_water_usage").attributes[
            ATTR_STATE_CLASS
        ]
        == SensorStateClass.TOTAL_INCREASING
    )

    assert hass.states.get("sensor.smart_water_shutoff_water_flow_rate").state == "0"
    assert (
        hass.states.get("sensor.smart_water_shutoff_water_flow_rate").attributes[
            ATTR_STATE_CLASS
        ]
        == SensorStateClass.MEASUREMENT
    )

    assert hass.states.get("sensor.smart_water_shutoff_water_pressure").state == "54.2"
    assert (
        hass.states.get("sensor.smart_water_shutoff_water_pressure").attributes[
            ATTR_STATE_CLASS
        ]
        == SensorStateClass.MEASUREMENT
    )

    assert hass.states.get("sensor.smart_water_shutoff_water_temperature").state == "70"
    assert (
        hass.states.get("sensor.smart_water_shutoff_water_temperature").attributes[
            ATTR_STATE_CLASS
        ]
        == SensorStateClass.MEASUREMENT
    )

    # and 3 entities for the detector
    assert hass.states.get("sensor.kitchen_sink_temperature").state == "61"
    assert (
        hass.states.get("sensor.kitchen_sink_temperature").attributes[ATTR_STATE_CLASS]
        == SensorStateClass.MEASUREMENT
    )

    assert hass.states.get("sensor.kitchen_sink_humidity").state == "43"
    assert (
        hass.states.get("sensor.kitchen_sink_humidity").attributes[ATTR_STATE_CLASS]
        == SensorStateClass.MEASUREMENT
    )

    assert hass.states.get("sensor.kitchen_sink_battery").state == "100"
    assert (
        hass.states.get("sensor.kitchen_sink_battery").attributes[ATTR_STATE_CLASS]
        == SensorStateClass.MEASUREMENT
    )