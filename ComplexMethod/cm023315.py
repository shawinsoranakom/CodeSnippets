async def test_leviton_zw4sf_fan(
    hass: HomeAssistant, client, leviton_zw4sf, integration
) -> None:
    """Test a Leviton ZW4SF fan with 4 fixed speeds."""
    node = leviton_zw4sf
    node_id = 88
    entity_id = "fan.4_speed_fan_controller"

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
    # 1 = 1-25, 2 = 26-49, 3 = 50-74, 4 = 75-99
    percentages_to_zwave_speeds = [
        [[0], [0]],
        [range(1, 26), range(1, 26)],
        [range(26, 51), range(26, 51)],
        [range(51, 76), range(51, 76)],
        [range(76, 101), range(76, 100)],
    ]

    for percentages, zwave_speeds in percentages_to_zwave_speeds:
        for percentage in percentages:
            actual_zwave_speed = await get_zwave_speed_from_percentage(percentage)
            assert actual_zwave_speed in zwave_speeds
        for zwave_speed in zwave_speeds:
            actual_percentage = await get_percentage_from_zwave_speed(zwave_speed)
            assert actual_percentage in percentages

    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_PERCENTAGE_STEP] == pytest.approx(25, rel=1e-3)
    assert state.attributes[ATTR_PRESET_MODES] == []