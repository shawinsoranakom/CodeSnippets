async def test_default_setup(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test all basic functionality of the rflink switch component."""
    # setup mocking rflink module
    event_callback, create, protocol, _ = await mock_rflink(
        hass, CONFIG, DOMAIN, monkeypatch
    )

    # make sure arguments are passed
    assert create.call_args_list[0][1]["ignore"]

    # test default state of switch loaded from config
    switch_initial = hass.states.get("switch.test")
    assert switch_initial.state == "off"
    assert switch_initial.attributes["assumed_state"]

    # switch should follow state of the hardware device by interpreting
    # incoming events for its name and aliases

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "on"})
    await hass.async_block_till_done()

    switch_after_first_command = hass.states.get("switch.test")
    assert switch_after_first_command.state == "on"
    # also after receiving first command state not longer has to be assumed
    assert not switch_after_first_command.attributes.get("assumed_state")

    # mock incoming command event for this device
    event_callback({"id": "protocol_0_0", "command": "off"})
    await hass.async_block_till_done()

    assert hass.states.get("switch.test").state == "off"

    # test following aliases
    # mock incoming command event for this device alias
    event_callback({"id": "test_alias_0_0", "command": "on"})
    await hass.async_block_till_done()

    assert hass.states.get("switch.test").state == "on"

    # The switch component does not support adding new devices for incoming
    # events because every new unknown device is added as a light by default.

    # test changing state from HA propagates to Rflink
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