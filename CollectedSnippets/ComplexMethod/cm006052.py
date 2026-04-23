async def test_shared_messages_isolated_between_users(
    client: AsyncClient, logged_in_headers, shared_messages_setup, user_two
):
    """User B cannot see User A's shared playground messages via API."""
    source_flow_id = shared_messages_setup["source_flow_id"]

    # User A can see their messages
    response_a = await client.get(
        f"api/v1/monitor/messages/shared?source_flow_id={source_flow_id}",
        headers=logged_in_headers,
    )
    assert response_a.status_code == status.HTTP_200_OK
    assert len(response_a.json()) == 4  # 3 in session-1 + 1 in session-2

    # Log in as User B
    login_data = {"username": user_two.username, "password": "hashed_password"}
    login_response = await client.post("api/v1/login", data=login_data)
    assert login_response.status_code == 200
    user_b_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    # User B sees EMPTY messages for the same source_flow_id
    response_b = await client.get(
        f"api/v1/monitor/messages/shared?source_flow_id={source_flow_id}",
        headers=user_b_headers,
    )
    assert response_b.status_code == status.HTTP_200_OK
    assert response_b.json() == []

    # User B also sees no sessions
    response_b_sessions = await client.get(
        f"api/v1/monitor/messages/shared/sessions?source_flow_id={source_flow_id}",
        headers=user_b_headers,
    )
    assert response_b_sessions.status_code == status.HTTP_200_OK
    assert response_b_sessions.json() == []