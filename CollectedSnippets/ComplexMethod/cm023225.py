async def test_light_color_only(
    hass: HomeAssistant, client, express_controls_ezmultipli, integration
) -> None:
    """Test the light entity for RGB lights with Color Switch CC only."""
    node = express_controls_ezmultipli
    state = hass.states.get(HSM200_V1_ENTITY)
    assert state.state == STATE_ON

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
                    "endpoint": 0,
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
                    "endpoint": 0,
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
                    "endpoint": 0,
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
                    "endpoint": 0,
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

    # Attempt to turn on the light and ensure it defaults to white
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 255, "green": 255, "blue": 255}

    client.async_send_command.reset_mock()

    # Force the light to turn off
    await update_color(0, 0, 0)

    state = hass.states.get(HSM200_V1_ENTITY)
    assert state.state == STATE_OFF

    # Force the light to turn on (50% green)
    await update_color(0, 128, 0)

    state = hass.states.get(HSM200_V1_ENTITY)
    assert state.state == STATE_ON

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 0, "green": 0, "blue": 0}

    client.async_send_command.reset_mock()

    # Force the light to turn off
    await update_color(0, 0, 0)

    # Assert that the last color is restored
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 0, "green": 128, "blue": 0}

    client.async_send_command.reset_mock()

    # Force the light to turn on (50% green)
    await update_color(0, 128, 0)

    state = hass.states.get(HSM200_V1_ENTITY)
    assert state.state == STATE_ON

    client.async_send_command.reset_mock()

    # Assert that the brightness is preserved when changing colors
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY, ATTR_RGB_COLOR: (255, 0, 0)},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 128, "green": 0, "blue": 0}

    client.async_send_command.reset_mock()

    # Force the light to turn on (50% red)
    await update_color(128, 0, 0)

    state = hass.states.get(HSM200_V1_ENTITY)
    assert state.state == STATE_ON

    # Assert that the color is preserved when changing brightness
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY, ATTR_BRIGHTNESS: 69},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 69, "green": 0, "blue": 0}

    client.async_send_command.reset_mock()

    await update_color(69, 0, 0)

    # Turn off again
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY},
        blocking=True,
    )
    await update_color(0, 0, 0)

    client.async_send_command.reset_mock()

    # Assert that the color is preserved when turning on with brightness
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY, ATTR_BRIGHTNESS: 123},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 123, "green": 0, "blue": 0}

    client.async_send_command.reset_mock()

    await update_color(123, 0, 0)

    # Turn off again
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY},
        blocking=True,
    )
    await update_color(0, 0, 0)

    # Turn off again and make sure last color/brightness is still preserved
    # when turning on light again in the next step
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY},
        blocking=True,
    )
    await update_color(0, 0, 0)

    client.async_send_command.reset_mock()

    # Assert that the brightness is preserved when turning on with color
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY, ATTR_HS_COLOR: (240, 100)},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 0, "green": 0, "blue": 123}

    client.async_send_command.reset_mock()

    await update_color(0, 0, 123)

    # Turn off twice
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY},
        blocking=True,
    )
    await update_color(0, 0, 0)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY},
        blocking=True,
    )
    await update_color(0, 0, 0)

    state = hass.states.get(HSM200_V1_ENTITY)
    assert state.state == STATE_OFF

    client.async_send_command.reset_mock()

    # Assert that turning on after successive off calls works and keeps the last color
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY, ATTR_BRIGHTNESS: 150},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 0, "green": 0, "blue": 150}

    client.async_send_command.reset_mock()

    await update_color(0, 0, 150)

    # Force the light to turn off
    await update_color(0, 0, 0)

    # Turn off already off light, we won't be aware of last color and brightness
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY},
        blocking=True,
    )
    await update_color(0, 0, 0)

    state = hass.states.get(HSM200_V1_ENTITY)
    assert state.state == STATE_OFF

    client.async_send_command.reset_mock()

    # Assert that turning on light after off call with unknown off color/brightness state
    # works and that light turns on to white with specified brightness
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY, ATTR_BRIGHTNESS: 160},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 160, "green": 160, "blue": 160}

    client.async_send_command.reset_mock()

    await update_color(160, 160, 160)

    # Clear the color value to trigger an unknown state
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Color Switch",
                "commandClass": 51,
                "endpoint": 0,
                "property": "currentColor",
                "newValue": None,
                "prevValue": None,
                "propertyName": "currentColor",
            },
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    state = hass.states.get(HSM200_V1_ENTITY)
    assert state.state == STATE_UNKNOWN

    client.async_send_command.reset_mock()

    # Assert that call fails if attribute is added to service call
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: HSM200_V1_ENTITY, ATTR_RGBW_COLOR: (255, 76, 255, 0)},
        blocking=True,
    )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 0,
        "property": "targetColor",
    }
    assert args["value"] == {"red": 255, "green": 76, "blue": 255}