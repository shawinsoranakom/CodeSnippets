async def test_evse_sensor(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test evse sensors."""
    # Test StateEnum value with binary_sensor.evse_charging_status
    entity_id = "binary_sensor.evse_charging_status"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "on"
    # switch to PluggedInDemand state
    set_node_attribute(matter_node, 1, 153, 0, 2)
    await trigger_subscription_callback(
        hass, matter_client, data=(matter_node.node_id, "1/153/0", 2)
    )
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "off"

    # Test StateEnum value with binary_sensor.evse_plug
    entity_id = "binary_sensor.evse_plug"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "on"
    # switch to NotPluggedIn state
    set_node_attribute(matter_node, 1, 153, 0, 0)
    await trigger_subscription_callback(
        hass, matter_client, data=(matter_node.node_id, "1/153/0", 0)
    )
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "off"

    # Test SupplyStateEnum value with binary_sensor.evse_charger_supply_state
    entity_id = "binary_sensor.evse_charger_supply_state"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "on"
    # switch to Disabled state
    set_node_attribute(matter_node, 1, 153, 1, 0)
    await trigger_subscription_callback(
        hass, matter_client, data=(matter_node.node_id, "1/153/1", 0)
    )
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "off"