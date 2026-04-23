async def test_reader_writer_create_partial_backup_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
    side_effect: Exception,
    error_code: str,
    error_message: str,
    expected_reason: str,
) -> None:
    """Test client partial backup error when generating a backup."""
    client = await hass_ws_client(hass)
    supervisor_client.backups.partial_backup.side_effect = side_effect

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {"type": "backup/generate", "agent_ids": ["hassio.local"], "name": "Test"}
    )
    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "create_backup",
        "reason": None,
        "stage": None,
        "state": "in_progress",
    }

    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "create_backup",
        "reason": expected_reason,
        "stage": None,
        "state": "failed",
    }

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}

    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == error_code
    assert response["error"]["message"] == error_message

    assert supervisor_client.backups.partial_backup.call_count == 1