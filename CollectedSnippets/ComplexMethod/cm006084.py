async def test_create_and_get_flow_events(client: AsyncClient, logged_in_headers):
    flow_id = await _create_flow(client, logged_in_headers)

    response = await client.post(
        f"api/v1/flows/{flow_id}/events",
        json={"type": "component_added", "summary": "Added OpenAI"},
        headers=logged_in_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    event = response.json()
    assert event["type"] == "component_added"
    assert event["summary"] == "Added OpenAI"
    assert "timestamp" in event

    response = await client.get(
        f"api/v1/flows/{flow_id}/events",
        params={"since": 0.0},
        headers=logged_in_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["events"]) == 1
    assert data["events"][0]["type"] == "component_added"
    assert data["settled"] is False