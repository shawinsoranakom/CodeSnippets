async def test_successfully_update_session_id(client, logged_in_headers, created_messages):
    old_session_id = "session_id2"
    new_session_id = "new_session_id"

    response = await client.patch(
        f"api/v1/monitor/messages/session/{old_session_id}",
        params={"new_session_id": new_session_id},
        headers=logged_in_headers,
    )

    assert response.status_code == 200, response.text
    updated_messages = response.json()
    assert len(updated_messages) == len(created_messages)
    for message in updated_messages:
        assert message["session_id"] == new_session_id

    response = await client.get(
        "api/v1/monitor/messages", headers=logged_in_headers, params={"session_id": new_session_id}
    )
    assert response.status_code == 200
    assert len(response.json()) == len(created_messages)
    messages = response.json()
    for message in messages:
        assert message["session_id"] == new_session_id
        response_timestamp = message["timestamp"]
        timestamp = datetime.strptime(response_timestamp, "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=timezone.utc)
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
        assert timestamp_str == response_timestamp

    # Check if the messages ordered by timestamp are in the correct order
    # User, User, AI
    assert messages[0]["sender"] == "User"
    assert messages[1]["sender"] == "User"
    assert messages[2]["sender"] == "AI"