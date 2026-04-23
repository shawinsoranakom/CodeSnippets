async def test_delete_messages_sessions_bulk(
    client: AsyncClient,
    created_messages_multiple_sessions,  # noqa: ARG001
    logged_in_headers,
):
    """Bulk-delete messages for multiple sessions in a single request."""
    session_ids = ["bulk_session_a", "bulk_session_b"]
    response = await client.request(
        "DELETE",
        "api/v1/monitor/messages/sessions",
        json=session_ids,
        headers=logged_in_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["deleted_count"] == 2
    assert "Messages deleted successfully" in data["message"]

    # Verify that messages for the deleted sessions are gone
    for sid in session_ids:
        response = await client.get("api/v1/monitor/messages", params={"session_id": sid}, headers=logged_in_headers)
        assert response.status_code == 200
        assert response.json() == [], f"Expected no messages for session {sid!r}"

    # Verify that messages for the untouched session are still present
    response = await client.get(
        "api/v1/monitor/messages", params={"session_id": "bulk_session_c"}, headers=logged_in_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 1