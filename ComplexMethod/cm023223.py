async def test_rgbw_light(hass: HomeAssistant, client, zen_31, integration) -> None:
    """Test the light entity."""
    state = hass.states.get(ZEN_31_ENTITY)

    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == LightEntityFeature.TRANSITION

    # Test turning on
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": ZEN_31_ENTITY, ATTR_RGBW_COLOR: (0, 0, 0, 128)},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 94
    assert args["valueId"] == {
        "commandClass": 51,
        "endpoint": 1,
        "property": "targetColor",
    }
    assert args["value"] == {"blue": 0, "green": 0, "red": 0, "warmWhite": 128}

    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 94
    assert args["valueId"] == {
        "commandClass": 38,
        "endpoint": 1,
        "property": "targetValue",
    }
    assert args["value"] == 255

    client.async_send_command.reset_mock()