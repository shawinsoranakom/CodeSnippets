async def test_power_sensor_inverted_availability(
    recorder_mock: Recorder, hass: HomeAssistant
) -> None:
    """Test inverted power sensor availability follows source sensor."""
    assert await async_setup_component(hass, "energy", {"energy": {}})
    manager = await async_get_manager(hass)
    manager.data = manager.default_preferences()

    # Set up source sensor as available
    hass.states.async_set("sensor.battery_power", "100.0")
    await hass.async_block_till_done()

    # Configure battery with inverted power_config
    await manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "battery",
                    "stat_energy_from": "sensor.battery_energy_from",
                    "stat_energy_to": "sensor.battery_energy_to",
                    "power_config": {
                        "stat_rate_inverted": "sensor.battery_power",
                    },
                }
            ],
        }
    )
    await hass.async_block_till_done()

    # Power sensor should be available
    state = hass.states.get("sensor.battery_power_inverted")
    assert state
    assert state.state == "-100.0"

    # Make source unavailable
    hass.states.async_set("sensor.battery_power", "unavailable")
    await hass.async_block_till_done()

    # Power sensor should become unavailable
    state = hass.states.get("sensor.battery_power_inverted")
    assert state
    assert state.state == "unavailable"

    # Make source available again
    hass.states.async_set("sensor.battery_power", "50.0")
    await hass.async_block_till_done()

    # Power sensor should become available again
    state = hass.states.get("sensor.battery_power_inverted")
    assert state
    assert state.state == "-50.0"