async def test_vacuum_updates(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test vacuum entity updates."""
    entity_id = "vacuum.mock_vacuum"
    state = hass.states.get(entity_id)
    assert state
    # confirm initial state is idle (as stored in the fixture)
    assert state.state == "idle"

    # confirm state is 'docked' by setting the operational state to 0x42
    set_node_attribute(matter_node, 1, 97, 4, 0x42)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "docked"

    # confirm state is 'docked' by setting the operational state to 0x41
    set_node_attribute(matter_node, 1, 97, 4, 0x41)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "docked"

    # confirm state is 'returning' by setting the operational state to 0x40
    set_node_attribute(matter_node, 1, 97, 4, 0x40)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "returning"

    # confirm state is 'idle' by setting the operational state to 0x01 (running) but mode is idle
    set_node_attribute(matter_node, 1, 97, 4, 0x01)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "idle"

    # confirm state is 'idle' by setting the operational state to 0x01 (running) but mode is cleaning
    set_node_attribute(matter_node, 1, 97, 4, 0x01)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "idle"

    # confirm state is 'paused' by setting the operational state to 0x02
    set_node_attribute(matter_node, 1, 97, 4, 0x02)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "paused"

    # confirm state is 'cleaning' by setting;
    # - the operational state to 0x00
    # - the run mode is set to a mode which has cleaning tag
    set_node_attribute(matter_node, 1, 97, 4, 0)
    set_node_attribute(matter_node, 1, 84, 1, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "cleaning"

    # confirm state is 'idle' by setting;
    # - the operational state to 0x00
    # - the run mode is set to a mode which has idle tag
    set_node_attribute(matter_node, 1, 97, 4, 0)
    set_node_attribute(matter_node, 1, 84, 1, 0)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "idle"

    # confirm state is 'cleaning' by setting;
    # - the operational state to 0x00
    # - the run mode is set to a mode which has mapping tag
    set_node_attribute(matter_node, 1, 97, 4, 0)
    set_node_attribute(matter_node, 1, 84, 1, 2)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "cleaning"

    # confirm state is 'unknown' by setting;
    # - the operational state to 0x00
    # - the run mode is set to a mode which has neither cleaning or idle tag
    set_node_attribute(matter_node, 1, 97, 4, 0)
    set_node_attribute(matter_node, 1, 84, 1, 5)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unknown"

    # confirm state is 'error' by setting;
    # - the operational state to 0x03
    set_node_attribute(matter_node, 1, 97, 4, 3)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "error"