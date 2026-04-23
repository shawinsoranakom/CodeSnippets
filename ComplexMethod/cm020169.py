async def test_reader_writer_create_wrong_parameters(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
    extra_generate_options: dict[str, Any],
    expected_error: dict[str, str],
) -> None:
    """Test generating a backup."""
    client = await hass_ws_client(hass)
    supervisor_client.backups.partial_backup.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.backup_info.return_value = TEST_BACKUP_DETAILS

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {"type": "backup/generate", "agent_ids": ["hassio.local"], "name": "Test"}
        | extra_generate_options
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
        "reason": "unknown_error",
        "stage": None,
        "state": "failed",
    }

    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "idle",
    }

    response = await client.receive_json()
    assert not response["success"]
    assert response["error"] == expected_error

    supervisor_client.backups.partial_backup.assert_not_called()