async def test_power_sensor_combined_invalid_value(
    recorder_mock: Recorder, hass: HomeAssistant
) -> None:
    """Test combined power sensor with invalid source value."""
    assert await async_setup_component(hass, "energy", {"energy": {}})
    manager = await async_get_manager(hass)
    manager.data = manager.default_preferences()

    # Set up both source sensors as valid
    hass.states.async_set("sensor.battery_discharge", "150.0")
    hass.states.async_set("sensor.battery_charge", "50.0")
    await hass.async_block_till_done()

    # Configure battery with combined power_config
    await manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "battery",
                    "stat_energy_from": "sensor.battery_energy_from",
                    "stat_energy_to": "sensor.battery_energy_to",
                    "power_config": {
                        "stat_rate_from": "sensor.battery_discharge",
                        "stat_rate_to": "sensor.battery_charge",
                    },
                }
            ],
        }
    )
    await hass.async_block_till_done()

    # Power sensor should be available
    state = hass.states.get(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )
    assert state
    assert state.state == "100.0"

    # Update first source to invalid value
    hass.states.async_set("sensor.battery_discharge", "invalid")
    await hass.async_block_till_done()

    # Power sensor should have unknown state (value is None)
    state = hass.states.get(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )
    assert state
    assert state.state == "unknown"

    # Restore first source
    hass.states.async_set("sensor.battery_discharge", "150.0")
    await hass.async_block_till_done()

    # Power sensor should work again
    state = hass.states.get(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )
    assert state
    assert state.state == "100.0"

    # Make second source invalid
    hass.states.async_set("sensor.battery_charge", "not_a_number")
    await hass.async_block_till_done()

    # Power sensor should have unknown state
    state = hass.states.get(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )
    assert state
    assert state.state == "unknown"