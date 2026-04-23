async def test_event_lifecycle(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the lifecycle of an event from upcoming to active to finished."""
    respx.get(CALENDER_URL).mock(
        return_value=Response(
            status_code=200,
            text=textwrap.dedent(
                """\
            BEGIN:VCALENDAR
            VERSION:2.0
            BEGIN:VEVENT
            SUMMARY:Test Event
            DTSTART:20230101T100000Z
            DTEND:20230101T110000Z
            END:VEVENT
            END:VCALENDAR
            """
            ),
        )
    )

    await setup_integration(hass, config_entry)

    # An upcoming event is off
    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes.get("message") == "Test Event"

    # Advance time to the start of the event
    freezer.move_to(datetime.fromisoformat("2023-01-01T10:00:00+00:00"))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # The event is active
    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get("message") == "Test Event"

    # Advance time to the end of the event
    freezer.move_to(datetime.fromisoformat("2023-01-01T11:00:00+00:00"))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # The event is finished
    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == STATE_OFF