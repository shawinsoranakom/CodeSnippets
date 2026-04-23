async def test_task_due_datetime(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test for task due at a specific time, using different time formats."""
    client = await hass_client()

    has_task_response = [
        get_events_response(
            {"dateTime": "2023-03-30T18:00:00-06:00"},
            {"dateTime": "2023-03-31T18:00:00-06:00"},
        )
    ]

    # Completely includes the start/end of the task
    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-30T08:00:00.000Z", "2023-03-31T08:00:00.000Z"
        ),
    )
    assert response.status == HTTPStatus.OK
    assert await response.json() == has_task_response

    # Overlap with the start of the event
    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-29T20:00:00.000Z", "2023-03-31T02:00:00.000Z"
        ),
    )
    assert response.status == HTTPStatus.OK
    assert await response.json() == has_task_response

    # Overlap with the end of the event
    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-31T20:00:00.000Z", "2023-04-01T02:00:00.000Z"
        ),
    )
    assert response.status == HTTPStatus.OK
    assert await response.json() == has_task_response

    # Task is active, but range does not include start/end
    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-31T10:00:00.000Z", "2023-03-31T11:00:00.000Z"
        ),
    )
    assert response.status == HTTPStatus.OK
    assert await response.json() == has_task_response

    # Query is before the task starts (no results)
    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-28T00:00:00.000Z", "2023-03-29T00:00:00.000Z"
        ),
    )
    assert response.status == HTTPStatus.OK
    assert await response.json() == []

    # Query is after the task ends (no results)
    response = await client.get(
        get_events_url(
            "calendar.name", "2023-04-01T07:00:00.000Z", "2023-04-02T07:00:00.000Z"
        ),
    )
    assert response.status == HTTPStatus.OK
    assert await response.json() == []