async def test_power_sensor_combined_availability(
    recorder_mock: Recorder, hass: HomeAssistant
) -> None:
    """Test combined power sensor availability requires both sources available."""
    assert await async_setup_component(hass, "energy", {"energy": {}})
    manager = await async_get_manager(hass)
    manager.data = manager.default_preferences()

    # Set up both source sensors as available
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

    # Power sensor should be available and show net power
    state = hass.states.get(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )
    assert state
    assert state.state == "100.0"

    # Make first source unavailable
    hass.states.async_set("sensor.battery_discharge", "unavailable")
    await hass.async_block_till_done()

    # Power sensor should become unavailable
    state = hass.states.get(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )
    assert state
    assert state.state == "unavailable"

    # Make first source available again
    hass.states.async_set("sensor.battery_discharge", "200.0")
    await hass.async_block_till_done()

    # Power sensor should become available again
    state = hass.states.get(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )
    assert state
    assert state.state == "150.0"

    # Make second source unavailable
    hass.states.async_set("sensor.battery_charge", "unknown")
    await hass.async_block_till_done()

    # Power sensor should become unavailable again
    state = hass.states.get(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )
    assert state
    assert state.state == "unavailable"