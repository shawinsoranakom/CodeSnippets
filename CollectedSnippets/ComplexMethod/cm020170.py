async def test_reader_writer_restore(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
    get_job_result: supervisor_jobs.Job,
    supervisor_events: list[dict[str, Any]],
) -> None:
    """Test restoring a backup."""
    client = await hass_ws_client(hass)
    supervisor_client.backups.partial_restore.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.list.return_value = [TEST_BACKUP]
    supervisor_client.backups.backup_info.return_value = TEST_BACKUP_DETAILS
    supervisor_client.jobs.get_job.return_value = get_job_result

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "idle",
    }
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {"type": "backup/restore", "agent_id": "hassio.local", "backup_id": "abc123"}
    )
    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "restore_backup",
        "reason": None,
        "stage": None,
        "state": "in_progress",
    }

    supervisor_client.backups.partial_restore.assert_called_once_with(
        "abc123",
        supervisor_backups.PartialRestoreOptions(
            addons=None,
            background=True,
            folders=None,
            homeassistant=True,
            location=LOCATION_LOCAL_STORAGE,
            password=None,
        ),
    )

    for event in supervisor_events:
        await client.send_json_auto_id({"type": "supervisor/event", "data": event})
        response = await client.receive_json()
        assert response["success"]

    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "restore_backup",
        "reason": None,
        "stage": None,
        "state": "completed",
    }

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}

    response = await client.receive_json()
    assert response["success"]
    assert response["result"] is None