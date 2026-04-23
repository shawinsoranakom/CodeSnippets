async def test_websocket_delete_recurring_event_instance(
    ws_client: ClientFixture,
    hass_client: ClientSessionGenerator,
    component_setup,
    mock_events_list: ApiResult,
    mock_events_list_items: ApiResult,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test websocket delete command with recurring events."""
    mock_events_list_items(
        [
            {
                **TEST_EVENT,
                "id": "event-id-1",
                "iCalUID": "event-id-1@google.com",
                "summary": "All Day Event",
                "start": {"date": "2022-10-08"},
                "end": {"date": "2022-10-09"},
                "recurrence": ["RRULE:FREQ=WEEKLY"],
            },
        ]
    )
    assert await component_setup()
    assert len(aioclient_mock.mock_calls) == 2

    # Get a time range for the first event and the second instance of the
    # recurring event.
    web_client = await hass_client()
    response = await web_client.get(
        get_events_url(TEST_ENTITY, "2022-10-06T00:00:00Z", "2022-10-20T00:00:00Z")
    )
    assert response.status == HTTPStatus.OK
    events = await response.json()
    assert len(events) == 2

    # Delete the second instance
    event = events[1]
    assert event["uid"] == "event-id-1@google.com"
    assert event["recurrence_id"] == "event-id-1_20221015"
    assert event["rrule"] == "FREQ=WEEKLY"

    # Expect a delete request as well as a follow up to sync state from server
    aioclient_mock.clear_requests()
    aioclient_mock.patch(
        f"{API_BASE_URL}/calendars/{CALENDAR_ID}/events/event-id-1_20221015"
    )
    mock_events_list_items([])

    client = await ws_client()
    await client.cmd_result(
        "delete",
        {
            "entity_id": TEST_ENTITY,
            "uid": event["uid"],
            "recurrence_id": event["recurrence_id"],
        },
    )

    assert len(aioclient_mock.mock_calls) == 2
    assert aioclient_mock.mock_calls[0][0] == "patch"
    # Request to cancel the second instance of the recurring event
    assert aioclient_mock.mock_calls[0][2] == {
        "id": "event-id-1_20221015",
        "status": "cancelled",
    }

    # Attempt delete again, but this time for all future instances
    aioclient_mock.clear_requests()
    aioclient_mock.patch(f"{API_BASE_URL}/calendars/{CALENDAR_ID}/events/event-id-1")
    mock_events_list_items([])

    client = await ws_client()
    await client.cmd_result(
        "delete",
        {
            "entity_id": TEST_ENTITY,
            "uid": event["uid"],
            "recurrence_id": event["recurrence_id"],
            "recurrence_range": "THISANDFUTURE",
        },
    )

    assert len(aioclient_mock.mock_calls) == 2
    assert aioclient_mock.mock_calls[0][0] == "patch"
    # Request to cancel all events after the second instance
    assert aioclient_mock.mock_calls[0][2] == {
        "id": "event-id-1",
        "recurrence": ["RRULE:FREQ=WEEKLY;UNTIL=20221014"],
    }