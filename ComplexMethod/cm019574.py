async def test_evse_sensor(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test evse sensors."""
    # EnergyEvseFaultState
    state = hass.states.get("sensor.evse_fault_state")
    assert state
    assert state.state == "no_error"

    set_node_attribute(matter_node, 1, 153, 2, 4)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.evse_fault_state")
    assert state
    assert state.state == "over_current"

    # EnergyEvseCircuitCapacity
    state = hass.states.get("sensor.evse_circuit_capacity")
    assert state
    assert state.state == "32.0"

    set_node_attribute(matter_node, 1, 153, 5, 63000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.evse_circuit_capacity")
    assert state
    assert state.state == "63.0"

    # EnergyEvseMinimumChargeCurrent
    state = hass.states.get("sensor.evse_min_charge_current")
    assert state
    assert state.state == "2.0"

    set_node_attribute(matter_node, 1, 153, 6, 5000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.evse_min_charge_current")
    assert state
    assert state.state == "5.0"

    # EnergyEvseMaximumChargeCurrent
    state = hass.states.get("sensor.evse_max_charge_current")
    assert state
    assert state.state == "30.0"

    set_node_attribute(matter_node, 1, 153, 7, 20000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.evse_max_charge_current")
    assert state
    assert state.state == "20.0"

    # EnergyEvseUserMaximumChargeCurrent
    state = hass.states.get("sensor.evse_user_max_charge_current")
    assert state
    assert state.state == "32.0"

    set_node_attribute(matter_node, 1, 153, 9, 63000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.evse_user_max_charge_current")
    assert state
    assert state.state == "63.0"