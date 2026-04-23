async def test_water_heater(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test water heater sensor."""
    # TankVolume
    state = hass.states.get("sensor.water_heater_tank_volume")
    assert state
    assert state.state == "200"

    set_node_attribute(matter_node, 2, 148, 2, 100)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.water_heater_tank_volume")
    assert state
    assert state.state == "100"

    # EstimatedHeatRequired
    state = hass.states.get("sensor.water_heater_required_heating_energy")
    assert state
    assert state.state == "4.0"

    set_node_attribute(matter_node, 2, 148, 3, 1000000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.water_heater_required_heating_energy")
    assert state
    assert state.state == "1.0"

    # TankPercentage
    state = hass.states.get("sensor.water_heater_hot_water_level")
    assert state
    assert state.state == "40"

    set_node_attribute(matter_node, 2, 148, 4, 50)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.water_heater_hot_water_level")
    assert state
    assert state.state == "50"

    # DeviceEnergyManagement -> ESAState attribute
    state = hass.states.get("sensor.water_heater_appliance_energy_state")
    assert state
    assert state.state == "online"

    set_node_attribute(matter_node, 2, 152, 2, 0)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.water_heater_appliance_energy_state")
    assert state
    assert state.state == "offline"

    # DeviceEnergyManagement -> OptOutState attribute
    state = hass.states.get("sensor.water_heater_energy_optimization_opt_out")
    assert state
    assert state.state == "no_opt_out"

    set_node_attribute(matter_node, 2, 152, 7, 3)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.water_heater_energy_optimization_opt_out")
    assert state
    assert state.state == "opt_out"