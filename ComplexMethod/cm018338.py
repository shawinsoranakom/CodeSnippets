async def test_pushed_relays_status_change(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """Test the relays cover changes its state on status received."""
    await init_integration(hass, entry)

    device_connection = get_device_connection(hass, (0, 7, False), entry)
    address = LcnAddr(0, 7, False)
    states = [False] * 8

    for entity_id in (COVER_RELAYS, COVER_RELAYS_BS4, COVER_RELAYS_MODULE):
        state = hass.states.get(entity_id)
        state.state = CoverState.CLOSED

    # push status "open"
    states[0:2] = [True, False]
    inp = ModStatusRelays(address, states)
    await device_connection.async_process_input(inp)
    await hass.async_block_till_done()

    state = hass.states.get(COVER_RELAYS)
    assert state is not None
    assert state.state == CoverState.OPENING

    # push status "stop"
    states[0] = False
    inp = ModStatusRelays(address, states)
    await device_connection.async_process_input(inp)
    await hass.async_block_till_done()

    state = hass.states.get(COVER_RELAYS)
    assert state is not None
    assert state.state not in (CoverState.OPENING, CoverState.CLOSING)

    # push status "close"
    states[0:2] = [True, True]
    inp = ModStatusRelays(address, states)
    await device_connection.async_process_input(inp)
    await hass.async_block_till_done()

    state = hass.states.get(COVER_RELAYS)
    assert state is not None
    assert state.state == CoverState.CLOSING

    # push status "set position" via BS4
    inp = ModStatusMotorPositionBS4(address, 1, 50)
    await device_connection.async_process_input(inp)
    await hass.async_block_till_done()

    state = hass.states.get(COVER_RELAYS_BS4)
    assert state is not None
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 50

    # push status "set position" via MODULE
    inp = ModStatusMotorPositionModule(address, 2, 75)
    await device_connection.async_process_input(inp)
    await hass.async_block_till_done()

    state = hass.states.get(COVER_RELAYS_MODULE)
    assert state is not None
    assert state.state == CoverState.OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 75