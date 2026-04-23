async def test_light_on_off_color(
    hass: HomeAssistant, client, logic_group_zdb5100, integration
) -> None:
    """Test the light entity for RGB lights without dimming support."""
    node = logic_group_zdb5100
    state = hass.states.get(ZDB5100_ENTITY)
    assert state.state == STATE_OFF

    async def update_color(red: int, green: int, blue: int) -> None:
        event = Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Color Switch",
                    "commandClass": 51,
                    "endpoint": 1,
                    "property": "currentColor",
                    "propertyKey": 2,  # red
                    "newValue": red,
                    "prevValue": None,
                    "propertyName": "currentColor",
                    "propertyKeyName": "red",
                },
            },
        )
        node.receive_event(event)
        await hass.async_block_till_done()

        event = Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Color Switch",
                    "commandClass": 51,
                    "endpoint": 1,
                    "property": "currentColor",
                    "propertyKey": 3,  # green
                    "newValue": green,
                    "prevValue": None,
                    "propertyName": "currentColor",
                    "propertyKeyName": "green",
                },
            },
        )
        node.receive_event(event)
        await hass.async_block_till_done()

        event = Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Color Switch",
                    "commandClass": 51,
                    "endpoint": 1,
                    "property": "currentColor",
                    "propertyKey": 4,  # blue
                    "newValue": blue,
                    "prevValue": None,
                    "propertyName": "currentColor",
                    "propertyKeyName": "blue",
                },
            },
        )
        node.receive_event(event)
        await hass.async_block_till_done()

        event = Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Color Switch",
                    "commandClass": 51,
                    "endpoint": 1,
                    "property": "currentColor",
                    "newValue": {
                        "red": red,
                        "green": green,
                        "blue": blue,
                    },
                    "prevValue": None,
                    "propertyName": "currentColor",
                },
            },
        )
        node.receive_event(event)
        await hass.async_block_till_done()

    async def update_switch_state(state: bool) -> None:
        event = Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Binary Switch",
                    "commandClass": 37,
                    "endpoint": 1,
                    "property": "currentValue",
                    "newValue": state,
                    "prevValue": None,
                    "propertyName": "currentValue",
                },
            },
        )
        node.receive_event(event)
        await hass.async_block_till_done()

    # Turn on the light. Since this is the first call, the light should default to white
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ZDB5100_ENTITY},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 1,
        "property": "targetColor",
    }
    assert args["value"] == {
        "red": 255,
        "green": 255,
        "blue": 255,
    }

    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 37,
        "endpoint": 1,
        "property": "targetValue",
    }
    assert args["value"] is True

    # Force the light to turn off
    await update_switch_state(False)

    state = hass.states.get(ZDB5100_ENTITY)
    assert state.state == STATE_OFF

    # Force the light to turn on (green)
    await update_color(0, 255, 0)
    await update_switch_state(True)

    state = hass.states.get(ZDB5100_ENTITY)
    assert state.state == STATE_ON

    client.async_send_command.reset_mock()

    # Set the brightness to 128. This should be encoded in the color value
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ZDB5100_ENTITY, ATTR_BRIGHTNESS: 128},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 1,
        "property": "targetColor",
    }
    assert args["value"] == {
        "red": 0,
        "green": 128,
        "blue": 0,
    }

    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 37,
        "endpoint": 1,
        "property": "targetValue",
    }
    assert args["value"] is True

    client.async_send_command.reset_mock()

    # Force the light to turn on (green, 50%)
    await update_color(0, 128, 0)

    # Set the color to red. This should preserve the previous brightness value
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ZDB5100_ENTITY, ATTR_HS_COLOR: (0, 100)},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 1,
        "property": "targetColor",
    }
    assert args["value"] == {
        "red": 128,
        "green": 0,
        "blue": 0,
    }

    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 37,
        "endpoint": 1,
        "property": "targetValue",
    }
    assert args["value"] is True

    client.async_send_command.reset_mock()

    # Force the light to turn on (red, 50%)
    await update_color(128, 0, 0)

    # Turn the device off. This should only affect the binary switch, not the color
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ZDB5100_ENTITY},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 37,
        "endpoint": 1,
        "property": "targetValue",
    }
    assert args["value"] is False

    client.async_send_command.reset_mock()

    # Force the light to turn off
    await update_switch_state(False)

    # Turn the device on again. This should only affect the binary switch, not the color
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ZDB5100_ENTITY},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 37,
        "endpoint": 1,
        "property": "targetValue",
    }
    assert args["value"] is True