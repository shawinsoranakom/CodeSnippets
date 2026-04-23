async def test_update_from_water_heater(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test enable boost from water heater device side."""
    entity_id = "water_heater.water_heater"

    # confirm initial BoostState (as stored in the fixture)
    state = hass.states.get(entity_id)
    assert state

    # confirm thermostat state is 'high_demand' by setting the BoostState to 1
    set_node_attribute(matter_node, 2, 148, 5, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_HIGH_DEMAND

    # confirm thermostat state is 'eco' by setting the BoostState to 0
    set_node_attribute(matter_node, 2, 148, 5, 0)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ECO

    # confirm water heater state is 'off' when SystemMode is set to 0 (kOff)
    set_node_attribute(matter_node, 2, 513, 28, 0)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    # confirm water heater state returns to 'eco' when SystemMode is set back to 4 (kHeat)
    set_node_attribute(matter_node, 2, 513, 28, 4)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ECO