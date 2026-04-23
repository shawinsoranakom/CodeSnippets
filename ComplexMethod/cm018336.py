async def test_fire_sendkeys_event(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Test the send_keys event is fired."""
    lcn_connection = await init_integration(hass, entry)
    events = async_capture_events(hass, LCN_SEND_KEYS)

    inp = ModSendKeysHost(
        LcnAddr(0, 7, False),
        actions=[SendKeyCommand.HIT, SendKeyCommand.MAKE, SendKeyCommand.DONTSEND],
        keys=[True, True, False, False, False, False, False, False],
    )

    await lcn_connection.async_process_input(inp)
    await hass.async_block_till_done()

    assert len(events) == 4
    assert events[0].event_type == LCN_SEND_KEYS
    assert events[0].data["key"] == "a1"
    assert events[0].data["action"] == "hit"
    assert events[1].event_type == LCN_SEND_KEYS
    assert events[1].data["key"] == "a2"
    assert events[1].data["action"] == "hit"
    assert events[2].event_type == LCN_SEND_KEYS
    assert events[2].data["key"] == "b1"
    assert events[2].data["action"] == "make"
    assert events[3].event_type == LCN_SEND_KEYS
    assert events[3].data["key"] == "b2"
    assert events[3].data["action"] == "make"