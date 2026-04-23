async def test_honeywell_39358_fan(
    hass: HomeAssistant, client, fan_honeywell_39358, integration
) -> None:
    """Test a Honeywell 39358 fan with 3 fixed speeds."""
    node = fan_honeywell_39358
    node_id = 61
    entity_id = "fan.honeywell_in_wall_smart_fan_control"

    async def get_zwave_speed_from_percentage(percentage):
        """Set the fan to a particular percentage and get the resulting Zwave speed."""
        client.async_send_command.reset_mock()

        await hass.services.async_call(
            "fan",
            "turn_on",
            {"entity_id": entity_id, "percentage": percentage},
            blocking=True,
        )

        assert len(client.async_send_command.call_args_list) == 1
        args = client.async_send_command.call_args[0][0]
        assert args["command"] == "node.set_value"
        assert args["nodeId"] == node_id
        return args["value"]

    async def get_percentage_from_zwave_speed(zwave_speed):
        """Set the underlying device speed and get the resulting percentage."""
        event = Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node_id,
                "args": {
                    "commandClassName": "Multilevel Switch",
                    "commandClass": 38,
                    "endpoint": 0,
                    "property": "currentValue",
                    "newValue": zwave_speed,
                    "prevValue": 0,
                    "propertyName": "currentValue",
                },
            },
        )
        node.receive_event(event)
        state = hass.states.get(entity_id)
        return state.attributes[ATTR_PERCENTAGE]

    # This device has the speeds:
    # low = 1-32, med = 33-66, high = 67-99
    percentages_to_zwave_speeds = [
        [[0], [0]],
        [range(1, 34), range(1, 33)],
        [range(34, 67), range(33, 67)],
        [range(67, 101), range(67, 100)],
    ]

    for percentages, zwave_speeds in percentages_to_zwave_speeds:
        for percentage in percentages:
            actual_zwave_speed = await get_zwave_speed_from_percentage(percentage)
            assert actual_zwave_speed in zwave_speeds
        for zwave_speed in zwave_speeds:
            actual_percentage = await get_percentage_from_zwave_speed(zwave_speed)
            assert actual_percentage in percentages

    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_PERCENTAGE_STEP] == pytest.approx(33.3333, rel=1e-3)
    assert state.attributes[ATTR_PRESET_MODES] == []