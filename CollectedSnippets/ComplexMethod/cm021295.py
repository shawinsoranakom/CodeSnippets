async def test_default_setup(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test all basic functionality of the RFLink switch component."""
    # setup mocking rflink module
    event_callback, create, protocol, _ = await mock_rflink(
        hass, CONFIG, DOMAIN, monkeypatch
    )

    # make sure arguments are passed
    assert create.call_args_list[0][1]["ignore"]

    # test default state of light loaded from config
    light_initial = hass.states.get(f"{DOMAIN}.test")
    assert light_initial.state == "off"
    assert light_initial.attributes["assumed_state"]

    # light should follow state of the hardware device by interpreting
    # incoming events for its name and aliases

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "on"})
    await hass.async_block_till_done()

    light_after_first_command = hass.states.get(f"{DOMAIN}.test")
    assert light_after_first_command.state == "on"
    # also after receiving first command state not longer has to be assumed
    assert not light_after_first_command.attributes.get("assumed_state")

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "off"})
    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.test").state == "off"

    # should respond to group command
    event_callback({"id": "protocol_0_0", "command": "allon"})
    await hass.async_block_till_done()

    light_after_first_command = hass.states.get(f"{DOMAIN}.test")
    assert light_after_first_command.state == "on"

    # should respond to group command
    event_callback({"id": "protocol_0_0", "command": "alloff"})
    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.test").state == "off"

    # test following aliases
    # mock incoming command event for this device alias
    event_callback({"id": "test_alias_0_0", "command": "on"})
    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.test").state == "on"

    # test event for new unconfigured sensor
    event_callback({"id": "protocol2_0_1", "command": "on"})
    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.protocol2_0_1").state == "on"

    # test changing state from HA propagates to RFLink
    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.async_block_till_done()
    assert hass.states.get(f"{DOMAIN}.test").state == "off"
    assert protocol.send_command_ack.call_args_list[0][0][0] == "protocol_0_0"
    assert protocol.send_command_ack.call_args_list[0][0][1] == "off"

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.async_block_till_done()
    assert hass.states.get(f"{DOMAIN}.test").state == "on"
    assert protocol.send_command_ack.call_args_list[1][0][1] == "on"

    # protocols supporting dimming and on/off should create hybrid light entity
    event_callback({"id": "newkaku_0_1", "command": "off"})
    await hass.async_block_till_done()
    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_0_1"}
    )
    await hass.async_block_till_done()

    # dimmable should send highest dim level when turning on
    assert protocol.send_command_ack.call_args_list[2][0][1] == "15"

    # and send on command for fallback
    assert protocol.send_command_ack.call_args_list[3][0][1] == "on"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: f"{DOMAIN}.newkaku_0_1", ATTR_BRIGHTNESS: 128},
    )
    await hass.async_block_till_done()

    assert protocol.send_command_ack.call_args_list[4][0][1] == "7"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: f"{DOMAIN}.dim_test", ATTR_BRIGHTNESS: 128},
    )
    await hass.async_block_till_done()

    assert protocol.send_command_ack.call_args_list[5][0][1] == "7"