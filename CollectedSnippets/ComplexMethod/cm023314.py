async def test_inovelli_lzw36(
    hass: HomeAssistant, client, inovelli_lzw36, integration
) -> None:
    """Test an LZW36."""
    node = inovelli_lzw36
    node_id = 19
    entity_id = "fan.family_room_combo_2"

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

    async def set_zwave_speed(zwave_speed):
        """Set the underlying device speed."""
        event = Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node_id,
                "args": {
                    "commandClassName": "Multilevel Switch",
                    "commandClass": 38,
                    "endpoint": 2,
                    "property": "currentValue",
                    "newValue": zwave_speed,
                    "prevValue": 0,
                    "propertyName": "currentValue",
                },
            },
        )
        node.receive_event(event)

    async def get_percentage_from_zwave_speed(zwave_speed):
        """Set the underlying device speed and get the resulting percentage."""
        await set_zwave_speed(zwave_speed)
        state = hass.states.get(entity_id)
        return state.attributes[ATTR_PERCENTAGE]

    # This device has the speeds:
    # low = 2-33, med = 34-66, high = 67-99
    percentages_to_zwave_speeds = [
        [[0], [0]],
        [range(1, 34), range(2, 34)],
        [range(34, 67), range(34, 67)],
        [range(67, 101), range(67, 100)],
    ]

    for percentages, zwave_speeds in percentages_to_zwave_speeds:
        for percentage in percentages:
            actual_zwave_speed = await get_zwave_speed_from_percentage(percentage)
            assert actual_zwave_speed in zwave_speeds
        for zwave_speed in zwave_speeds:
            actual_percentage = await get_percentage_from_zwave_speed(zwave_speed)
            assert actual_percentage in percentages

    # Check static entity properties
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_PERCENTAGE_STEP] == pytest.approx(33.3333, rel=1e-3)
    assert state.attributes[ATTR_PRESET_MODES] == ["breeze"]

    # This device has one preset, where a device level of "1" is the
    # "breeze" mode
    await set_zwave_speed(1)
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_PRESET_MODE] == "breeze"
    assert state.attributes[ATTR_PERCENTAGE] is None

    client.async_send_command.reset_mock()

    await hass.services.async_call(
        "fan",
        "turn_on",
        {"entity_id": entity_id, "preset_mode": "breeze"},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == node_id
    assert args["value"] == 1

    client.async_send_command.reset_mock()
    with pytest.raises(NotValidPresetModeError) as exc:
        await hass.services.async_call(
            "fan",
            "turn_on",
            {"entity_id": entity_id, "preset_mode": "wheeze"},
            blocking=True,
        )
    assert exc.value.translation_key == "not_valid_preset_mode"
    assert len(client.async_send_command.call_args_list) == 0