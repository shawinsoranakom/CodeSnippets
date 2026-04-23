async def test_door_lock(
    hass: HomeAssistant,
    client,
    lock_schlage_be469,
    integration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a lock entity with door lock command class."""
    node = lock_schlage_be469
    state = hass.states.get(SCHLAGE_BE469_LOCK_ENTITY)

    assert state
    assert state.state == LockState.UNLOCKED

    # Test locking
    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_LOCK,
        {ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 20
    assert args["valueId"] == {
        "commandClass": 98,
        "endpoint": 0,
        "property": "targetMode",
    }
    assert args["value"] == 255

    client.async_send_command.reset_mock()

    # Test locked update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 20,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 98,
                "endpoint": 0,
                "property": "currentMode",
                "newValue": 255,
                "prevValue": 0,
                "propertyName": "currentMode",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(SCHLAGE_BE469_LOCK_ENTITY)
    assert state
    assert state.state == LockState.LOCKED

    client.async_send_command.reset_mock()

    # Test unlocking
    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_UNLOCK,
        {ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 20
    assert args["valueId"] == {
        "commandClass": 98,
        "endpoint": 0,
        "property": "targetMode",
    }
    assert args["value"] == 0

    client.async_send_command.reset_mock()

    # Test set usercode service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_LOCK_USERCODE,
        {
            ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY,
            ATTR_CODE_SLOT: 1,
            ATTR_USERCODE: "1234",
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 20
    assert args["valueId"] == {
        "commandClass": 99,
        "endpoint": 0,
        "property": "userCode",
        "propertyKey": 1,
    }
    assert args["value"] == "1234"

    client.async_send_command.reset_mock()

    # Test clear usercode
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLEAR_LOCK_USERCODE,
        {ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY, ATTR_CODE_SLOT: 1},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 20
    assert args["valueId"] == {
        "commandClass": 99,
        "endpoint": 0,
        "property": "userIdStatus",
        "propertyKey": 1,
    }
    assert args["value"] == 0

    client.async_send_command.reset_mock()

    # Test get usercode
    with patch(
        "homeassistant.components.zwave_js.lock.get_usercode",
        return_value={
            "code_slot": 1,
            "name": "test",
            "in_use": True,
            "usercode": "1234",
        },
    ) as mock_get_usercode:
        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_LOCK_USERCODE,
            {ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY, ATTR_CODE_SLOT: 1},
            blocking=True,
            return_response=True,
        )
        mock_get_usercode.assert_called_once()
        args = mock_get_usercode.call_args[0]
        assert args[0].node_id == 20
        assert args[1] == 1
        assert response == {
            SCHLAGE_BE469_LOCK_ENTITY: {
                "1": {
                    "usercode": "1234",
                    "in_use": True,
                },
            }
        }

    # Test set configuration
    client.async_send_command.return_value = {
        "response": {"status": 1, "remainingDuration": "default"}
    }
    caplog.clear()
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_LOCK_CONFIGURATION,
        {
            ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY,
            ATTR_OPERATION_TYPE: "timed",
            ATTR_LOCK_TIMEOUT: 1,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["nodeId"] == 20
    assert args["endpoint"] == 0
    assert args["args"] == [
        {
            "insideHandlesCanOpenDoorConfiguration": [True, True, True, True],
            "operationType": 2,
            "outsideHandlesCanOpenDoorConfiguration": [True, True, True, True],
            "lockTimeoutConfiguration": 1,
        }
    ]
    assert args["commandClass"] == 98
    assert args["methodName"] == "setConfiguration"
    assert "Result status" in caplog.text
    assert "remaining duration" in caplog.text
    assert "setting lock configuration" in caplog.text

    client.async_send_command.reset_mock()
    client.async_send_command_no_wait.reset_mock()
    caplog.clear()

    # Put node to sleep and validate that we don't wait for a return or log anything
    event = Event(
        "sleep",
        {
            "source": "node",
            "event": "sleep",
            "nodeId": node.node_id,
        },
    )
    node.receive_event(event)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_LOCK_CONFIGURATION,
        {
            ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY,
            ATTR_OPERATION_TYPE: "timed",
            ATTR_LOCK_TIMEOUT: 1,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 0
    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["nodeId"] == 20
    assert args["endpoint"] == 0
    assert args["args"] == [
        {
            "insideHandlesCanOpenDoorConfiguration": [True, True, True, True],
            "operationType": 2,
            "outsideHandlesCanOpenDoorConfiguration": [True, True, True, True],
            "lockTimeoutConfiguration": 1,
        }
    ]
    assert args["commandClass"] == 98
    assert args["methodName"] == "setConfiguration"
    assert "Result status" not in caplog.text
    assert "remaining duration" not in caplog.text
    assert "setting lock configuration" not in caplog.text

    # Mark node as alive
    event = Event(
        "alive",
        {
            "source": "node",
            "event": "alive",
            "nodeId": node.node_id,
        },
    )
    node.receive_event(event)

    client.async_send_command.side_effect = FailedZWaveCommand("test", 1, "test")
    # Test set usercode service error handling
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_LOCK_USERCODE,
            {
                ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY,
                ATTR_CODE_SLOT: 1,
                ATTR_USERCODE: "1234",
            },
            blocking=True,
        )

    # Test clear usercode service error handling
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CLEAR_LOCK_USERCODE,
            {ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY, ATTR_CODE_SLOT: 1},
            blocking=True,
        )

    # Test get usercode service error handling
    with (
        patch(
            "homeassistant.components.zwave_js.lock.get_usercode",
            side_effect=NotFoundError("usercode for code slot 1 not found"),
        ),
        pytest.raises(HomeAssistantError),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_LOCK_USERCODE,
            {ATTR_ENTITY_ID: SCHLAGE_BE469_LOCK_ENTITY, ATTR_CODE_SLOT: 1},
            blocking=True,
            return_response=True,
        )

    client.async_send_command.reset_mock()

    event = Event(
        type="dead",
        data={
            "source": "node",
            "event": "dead",
            "nodeId": 20,
        },
    )
    node.receive_event(event)

    assert node.status == NodeStatus.DEAD
    state = hass.states.get(SCHLAGE_BE469_LOCK_ENTITY)
    assert state
    # The state should still be locked, even if the node is dead
    assert state.state == LockState.LOCKED