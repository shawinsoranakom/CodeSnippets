async def test_inverted_cover(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure states are restored on startup."""
    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "nonkaku_device_1": {
                    "name": "nonkaku_type_standard",
                    "type": "standard",
                },
                "nonkaku_device_2": {"name": "nonkaku_type_none"},
                "nonkaku_device_3": {
                    "name": "nonkaku_type_inverted",
                    "type": "inverted",
                },
                "newkaku_device_4": {
                    "name": "newkaku_type_standard",
                    "type": "standard",
                },
                "newkaku_device_5": {"name": "newkaku_type_none"},
                "newkaku_device_6": {
                    "name": "newkaku_type_inverted",
                    "type": "inverted",
                },
            },
        },
    }

    # setup mocking rflink module
    event_callback, _, protocol, _ = await mock_rflink(
        hass, config, DOMAIN, monkeypatch
    )

    # test default state of cover loaded from config
    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_standard")
    assert standard_cover.state == CoverState.CLOSED
    assert standard_cover.attributes["assumed_state"]

    # mock incoming up command event for nonkaku_device_1
    event_callback({"id": "nonkaku_device_1", "command": "up"})
    await hass.async_block_till_done()

    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_standard")
    assert standard_cover.state == CoverState.OPEN
    assert standard_cover.attributes.get("assumed_state")

    # mock incoming up command event for nonkaku_device_2
    event_callback({"id": "nonkaku_device_2", "command": "up"})
    await hass.async_block_till_done()

    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_none")
    assert standard_cover.state == CoverState.OPEN
    assert standard_cover.attributes.get("assumed_state")

    # mock incoming up command event for nonkaku_device_3
    event_callback({"id": "nonkaku_device_3", "command": "up"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_inverted")
    assert inverted_cover.state == CoverState.OPEN
    assert inverted_cover.attributes.get("assumed_state")

    # mock incoming up command event for newkaku_device_4
    event_callback({"id": "newkaku_device_4", "command": "up"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_standard")
    assert inverted_cover.state == CoverState.OPEN
    assert inverted_cover.attributes.get("assumed_state")

    # mock incoming up command event for newkaku_device_5
    event_callback({"id": "newkaku_device_5", "command": "up"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_none")
    assert inverted_cover.state == CoverState.OPEN
    assert inverted_cover.attributes.get("assumed_state")

    # mock incoming up command event for newkaku_device_6
    event_callback({"id": "newkaku_device_6", "command": "up"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_inverted")
    assert inverted_cover.state == CoverState.OPEN
    assert inverted_cover.attributes.get("assumed_state")

    # mock incoming down command event for nonkaku_device_1
    event_callback({"id": "nonkaku_device_1", "command": "down"})

    await hass.async_block_till_done()

    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_standard")
    assert standard_cover.state == CoverState.CLOSED
    assert standard_cover.attributes.get("assumed_state")

    # mock incoming down command event for nonkaku_device_2
    event_callback({"id": "nonkaku_device_2", "command": "down"})

    await hass.async_block_till_done()

    standard_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_none")
    assert standard_cover.state == CoverState.CLOSED
    assert standard_cover.attributes.get("assumed_state")

    # mock incoming down command event for nonkaku_device_3
    event_callback({"id": "nonkaku_device_3", "command": "down"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_inverted")
    assert inverted_cover.state == CoverState.CLOSED
    assert inverted_cover.attributes.get("assumed_state")

    # mock incoming down command event for newkaku_device_4
    event_callback({"id": "newkaku_device_4", "command": "down"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_standard")
    assert inverted_cover.state == CoverState.CLOSED
    assert inverted_cover.attributes.get("assumed_state")

    # mock incoming down command event for newkaku_device_5
    event_callback({"id": "newkaku_device_5", "command": "down"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_none")
    assert inverted_cover.state == CoverState.CLOSED
    assert inverted_cover.attributes.get("assumed_state")

    # mock incoming down command event for newkaku_device_6
    event_callback({"id": "newkaku_device_6", "command": "down"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_inverted")
    assert inverted_cover.state == CoverState.CLOSED
    assert inverted_cover.attributes.get("assumed_state")

    # We are only testing the 'inverted' devices, the 'standard' devices
    # are already covered by other test cases.

    # should respond to group command
    event_callback({"id": "nonkaku_device_3", "command": "alloff"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_inverted")
    assert inverted_cover.state == CoverState.CLOSED

    # should respond to group command
    event_callback({"id": "nonkaku_device_3", "command": "allon"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.nonkaku_type_inverted")
    assert inverted_cover.state == CoverState.OPEN

    # should respond to group command
    event_callback({"id": "newkaku_device_4", "command": "alloff"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_standard")
    assert inverted_cover.state == CoverState.CLOSED

    # should respond to group command
    event_callback({"id": "newkaku_device_4", "command": "allon"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_standard")
    assert inverted_cover.state == CoverState.OPEN

    # should respond to group command
    event_callback({"id": "newkaku_device_5", "command": "alloff"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_none")
    assert inverted_cover.state == CoverState.CLOSED

    # should respond to group command
    event_callback({"id": "newkaku_device_5", "command": "allon"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_none")
    assert inverted_cover.state == CoverState.OPEN

    # should respond to group command
    event_callback({"id": "newkaku_device_6", "command": "alloff"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_inverted")
    assert inverted_cover.state == CoverState.CLOSED

    # should respond to group command
    event_callback({"id": "newkaku_device_6", "command": "allon"})

    await hass.async_block_till_done()

    inverted_cover = hass.states.get(f"{DOMAIN}.newkaku_type_inverted")
    assert inverted_cover.state == CoverState.OPEN

    # Sending the close command from HA should result
    # in an 'DOWN' command sent to a non-newkaku device
    # that has its type set to 'standard'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_standard"},
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.nonkaku_type_standard").state == CoverState.CLOSED
    assert protocol.send_command_ack.call_args_list[0][0][0] == "nonkaku_device_1"
    assert protocol.send_command_ack.call_args_list[0][0][1] == "DOWN"

    # Sending the open command from HA should result
    # in an 'UP' command sent to a non-newkaku device
    # that has its type set to 'standard'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_standard"},
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.nonkaku_type_standard").state == CoverState.OPEN
    assert protocol.send_command_ack.call_args_list[1][0][0] == "nonkaku_device_1"
    assert protocol.send_command_ack.call_args_list[1][0][1] == "UP"

    # Sending the close command from HA should result
    # in an 'DOWN' command sent to a non-newkaku device
    # that has its type not specified.
    await hass.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_none"}
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.nonkaku_type_none").state == CoverState.CLOSED
    assert protocol.send_command_ack.call_args_list[2][0][0] == "nonkaku_device_2"
    assert protocol.send_command_ack.call_args_list[2][0][1] == "DOWN"

    # Sending the open command from HA should result
    # in an 'UP' command sent to a non-newkaku device
    # that has its type not specified.
    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_none"}
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.nonkaku_type_none").state == CoverState.OPEN
    assert protocol.send_command_ack.call_args_list[3][0][0] == "nonkaku_device_2"
    assert protocol.send_command_ack.call_args_list[3][0][1] == "UP"

    # Sending the close command from HA should result
    # in an 'UP' command sent to a non-newkaku device
    # that has its type set to 'inverted'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_inverted"},
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.nonkaku_type_inverted").state == CoverState.CLOSED
    assert protocol.send_command_ack.call_args_list[4][0][0] == "nonkaku_device_3"
    assert protocol.send_command_ack.call_args_list[4][0][1] == "UP"

    # Sending the open command from HA should result
    # in an 'DOWN' command sent to a non-newkaku device
    # that has its type set to 'inverted'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.nonkaku_type_inverted"},
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.nonkaku_type_inverted").state == CoverState.OPEN
    assert protocol.send_command_ack.call_args_list[5][0][0] == "nonkaku_device_3"
    assert protocol.send_command_ack.call_args_list[5][0][1] == "DOWN"

    # Sending the close command from HA should result
    # in an 'DOWN' command sent to a newkaku device
    # that has its type set to 'standard'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_standard"},
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.newkaku_type_standard").state == CoverState.CLOSED
    assert protocol.send_command_ack.call_args_list[6][0][0] == "newkaku_device_4"
    assert protocol.send_command_ack.call_args_list[6][0][1] == "DOWN"

    # Sending the open command from HA should result
    # in an 'UP' command sent to a newkaku device
    # that has its type set to 'standard'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_standard"},
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.newkaku_type_standard").state == CoverState.OPEN
    assert protocol.send_command_ack.call_args_list[7][0][0] == "newkaku_device_4"
    assert protocol.send_command_ack.call_args_list[7][0][1] == "UP"

    # Sending the close command from HA should result
    # in an 'UP' command sent to a newkaku device
    # that has its type not specified.
    await hass.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_none"}
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.newkaku_type_none").state == CoverState.CLOSED
    assert protocol.send_command_ack.call_args_list[8][0][0] == "newkaku_device_5"
    assert protocol.send_command_ack.call_args_list[8][0][1] == "UP"

    # Sending the open command from HA should result
    # in an 'DOWN' command sent to a newkaku device
    # that has its type not specified.
    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_none"}
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.newkaku_type_none").state == CoverState.OPEN
    assert protocol.send_command_ack.call_args_list[9][0][0] == "newkaku_device_5"
    assert protocol.send_command_ack.call_args_list[9][0][1] == "DOWN"

    # Sending the close command from HA should result
    # in an 'UP' command sent to a newkaku device
    # that has its type set to 'inverted'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_inverted"},
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.newkaku_type_inverted").state == CoverState.CLOSED
    assert protocol.send_command_ack.call_args_list[10][0][0] == "newkaku_device_6"
    assert protocol.send_command_ack.call_args_list[10][0][1] == "UP"

    # Sending the open command from HA should result
    # in an 'DOWN' command sent to a newkaku device
    # that has its type set to 'inverted'.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_type_inverted"},
    )

    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.newkaku_type_inverted").state == CoverState.OPEN
    assert protocol.send_command_ack.call_args_list[11][0][0] == "newkaku_device_6"
    assert protocol.send_command_ack.call_args_list[11][0][1] == "DOWN"