async def test_invalid_rrule_fix(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_events_list_items,
    component_setup,
) -> None:
    """Test that an invalid RRULE returned from Google Calendar API is handled correctly end to end."""
    week_from_today = dt_util.now().date() + datetime.timedelta(days=7)
    end_event = week_from_today + datetime.timedelta(days=1)
    event = {
        **TEST_EVENT,
        "start": {"date": week_from_today.isoformat()},
        "end": {"date": end_event.isoformat()},
        "recurrence": [
            "RRULE:DATE;TZID=Europe/Warsaw:20230818T020000,20230915T020000,20231013T020000,20231110T010000,20231208T010000",
        ],
    }
    mock_events_list_items([event])

    assert await component_setup()

    state = hass.states.get(TEST_ENTITY)
    assert state.name == TEST_ENTITY_NAME
    assert state.state == STATE_OFF

    # Pick a date range that contains two instances of the event
    web_client = await hass_client()
    response = await web_client.get(
        get_events_url(TEST_ENTITY, "2023-08-10T00:00:00Z", "2023-09-20T00:00:00Z")
    )
    assert response.status == HTTPStatus.OK
    events = await response.json()

    # Both instances are returned, however the RDATE rule is ignored by Home
    # Assistant so they are just treateded as flattened events.
    assert len(events) == 2

    event = events[0]
    assert event["uid"] == "cydrevtfuybguinhomj@google.com"
    assert event["recurrence_id"] == "_c8rinwq863h45qnucyoi43ny8_20230818"
    assert event["rrule"] is None

    event = events[1]
    assert event["uid"] == "cydrevtfuybguinhomj@google.com"
    assert event["recurrence_id"] == "_c8rinwq863h45qnucyoi43ny8_20230915"
    assert event["rrule"] is None