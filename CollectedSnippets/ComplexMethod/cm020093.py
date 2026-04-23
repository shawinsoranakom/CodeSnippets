async def test_event_register(hass: HomeAssistant, knx: KNXTestKit) -> None:
    """Test `knx.event_register` service."""
    events = async_capture_events(hass, "knx_event")
    test_address = "1/2/3"

    await knx.setup_integration()

    # no event registered
    await knx.receive_write(test_address, True)
    assert len(events) == 0

    # register event with `type`
    await hass.services.async_call(
        "knx",
        "event_register",
        {"address": test_address, "type": "2byte_unsigned"},
        blocking=True,
    )
    await knx.receive_write(test_address, (0x04, 0xD2))
    assert len(events) == 1
    typed_event = events.pop()
    assert typed_event.data["data"] == (0x04, 0xD2)
    assert typed_event.data["value"] == 1234

    # remove event registration - no event added
    await hass.services.async_call(
        "knx",
        "event_register",
        {"address": test_address, "remove": True},
        blocking=True,
    )
    await knx.receive_write(test_address, True)
    assert len(events) == 0

    # register event without `type`
    await hass.services.async_call(
        "knx", "event_register", {"address": test_address}, blocking=True
    )
    await knx.receive_write(test_address, True)
    await knx.receive_write(test_address, False)
    assert len(events) == 2
    untyped_event_2 = events.pop()
    assert untyped_event_2.data["data"] is False
    assert untyped_event_2.data["value"] is None
    untyped_event_1 = events.pop()
    assert untyped_event_1.data["data"] is True
    assert untyped_event_1.data["value"] is None