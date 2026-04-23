async def test_default_setup(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test all basic functionality of the RFLink cover component."""
    # setup mocking rflink module
    event_callback, create, protocol, _ = await mock_rflink(
        hass, CONFIG, DOMAIN, monkeypatch
    )

    # make sure arguments are passed
    assert create.call_args_list[0][1]["ignore"]

    # test default state of cover loaded from config
    cover_initial = hass.states.get(f"{DOMAIN}.test")
    assert cover_initial.state == CoverState.CLOSED
    assert cover_initial.attributes["assumed_state"]

    # cover should follow state of the hardware device by interpreting
    # incoming events for its name and aliases

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "up"})
    await hass.async_block_till_done()

    cover_after_first_command = hass.states.get(f"{DOMAIN}.test")
    assert cover_after_first_command.state == CoverState.OPEN
    # not sure why, but cover have always assumed_state=true
    assert cover_after_first_command.attributes.get("assumed_state")

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "down"})
    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.test").state == CoverState.CLOSED

    # should respond to group command
    event_callback({"id": "protocol_0_0", "command": "allon"})
    await hass.async_block_till_done()

    cover_after_first_command = hass.states.get(f"{DOMAIN}.test")
    assert cover_after_first_command.state == CoverState.OPEN

    # should respond to group command
    event_callback({"id": "protocol_0_0", "command": "alloff"})
    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.test").state == CoverState.CLOSED

    # test following aliases
    # mock incoming command event for this device alias
    event_callback({"id": "test_alias_0_0", "command": "up"})
    await hass.async_block_till_done()

    assert hass.states.get(f"{DOMAIN}.test").state == CoverState.OPEN

    # test changing state from HA propagates to RFLink
    await hass.services.async_call(
        DOMAIN, SERVICE_CLOSE_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.async_block_till_done()
    assert hass.states.get(f"{DOMAIN}.test").state == CoverState.CLOSED
    assert protocol.send_command_ack.call_args_list[0][0][0] == "protocol_0_0"
    assert protocol.send_command_ack.call_args_list[0][0][1] == "DOWN"

    await hass.services.async_call(
        DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: f"{DOMAIN}.test"}
    )
    await hass.async_block_till_done()
    assert hass.states.get(f"{DOMAIN}.test").state == CoverState.OPEN
    assert protocol.send_command_ack.call_args_list[1][0][1] == "UP"