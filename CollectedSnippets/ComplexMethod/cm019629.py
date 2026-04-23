async def test_lock(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test door lock."""
    await hass.services.async_call(
        "lock",
        "unlock",
        {
            "entity_id": "lock.mock_door_lock",
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.DoorLock.Commands.UnlockDoor(),
        timed_request_timeout_ms=10000,
    )
    matter_client.send_device_command.reset_mock()

    await hass.services.async_call(
        "lock",
        "lock",
        {
            "entity_id": "lock.mock_door_lock",
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.DoorLock.Commands.LockDoor(),
        timed_request_timeout_ms=10000,
    )
    matter_client.send_device_command.reset_mock()

    await hass.async_block_till_done()
    state = hass.states.get("lock.mock_door_lock")
    assert state
    assert state.state == LockState.LOCKING

    set_node_attribute(matter_node, 1, 257, 0, 0)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("lock.mock_door_lock")
    assert state
    assert state.state == LockState.UNLOCKED

    set_node_attribute(matter_node, 1, 257, 0, 2)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("lock.mock_door_lock")
    assert state
    assert state.state == LockState.UNLOCKED

    set_node_attribute(matter_node, 1, 257, 0, 1)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("lock.mock_door_lock")
    assert state
    assert state.state == LockState.LOCKED

    set_node_attribute(matter_node, 1, 257, 0, None)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("lock.mock_door_lock")
    assert state
    assert state.state == STATE_UNKNOWN

    # test featuremap update
    set_node_attribute(matter_node, 1, 257, 65532, 4096)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("lock.mock_door_lock")
    assert state.attributes["supported_features"] & LockEntityFeature.OPEN

    # test handling of a node LockOperation event
    await trigger_subscription_callback(
        hass,
        matter_client,
        EventType.NODE_EVENT,
        MatterNodeEvent(
            node_id=matter_node.node_id,
            endpoint_id=1,
            cluster_id=257,
            event_id=2,
            event_number=0,
            priority=1,
            timestamp=0,
            timestamp_type=0,
            data={"operationSource": 3},
        ),
    )
    state = hass.states.get("lock.mock_door_lock")
    assert state.attributes[ATTR_CHANGED_BY] == "Keypad"