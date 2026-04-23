async def test_api_date_time_event(
    get_events: GetEventsFn,
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    ics_content: str,
) -> None:
    """Test an event with a start/end date time."""
    respx.get(CALENDER_URL).mock(
        return_value=Response(
            status_code=200,
            text=ics_content,
        )
    )
    await setup_integration(hass, config_entry)
    events = await get_events("1997-07-14T00:00:00Z", "1997-07-16T00:00:00Z")
    assert list(map(event_fields, events)) == [
        {
            "summary": "Bastille Day Party",
            "start": {"dateTime": "1997-07-14T11:00:00-06:00"},
            "end": {"dateTime": "1997-07-14T22:00:00-06:00"},
        }
    ]

    # Query events in UTC

    # Time range before event
    events = await get_events("1997-07-13T00:00:00Z", "1997-07-14T16:00:00Z")
    assert len(events) == 0
    # Time range after event
    events = await get_events("1997-07-15T05:00:00Z", "1997-07-15T06:00:00Z")
    assert len(events) == 0

    # Overlap with event start
    events = await get_events("1997-07-13T00:00:00Z", "1997-07-14T18:00:00Z")
    assert len(events) == 1
    # Overlap with event end
    events = await get_events("1997-07-15T03:00:00Z", "1997-07-15T06:00:00Z")
    assert len(events) == 1

    # Query events overlapping with start and end but in another timezone
    events = await get_events("1997-07-12T23:00:00-01:00", "1997-07-14T17:00:00-01:00")
    assert len(events) == 1
    events = await get_events("1997-07-15T02:00:00-01:00", "1997-07-15T05:00:00-01:00")
    assert len(events) == 1