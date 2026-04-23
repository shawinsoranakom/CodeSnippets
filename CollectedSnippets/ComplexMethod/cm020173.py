async def test_reader_writer_restore_late_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
) -> None:
    """Test restoring a backup with error."""
    client = await hass_ws_client(hass)
    supervisor_client.backups.partial_restore.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.list.return_value = [TEST_BACKUP]
    supervisor_client.backups.backup_info.return_value = TEST_BACKUP_DETAILS
    supervisor_client.jobs.get_job.return_value = TEST_JOB_NOT_DONE

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
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

    event = {
        "event": "job",
        "data": {
            "name": "backup_manager_partial_restore",
            "reference": "7c54aeed",
            "uuid": TEST_JOB_ID,
            "progress": 0,
            "stage": None,
            "done": True,
            "parent_id": None,
            "errors": [
                {
                    "type": "BackupInvalidError",
                    "message": (
                        "Backup was made on supervisor version 2025.02.2.dev3105, can't"
                        " restore on 2025.01.2.dev3105. Must update supervisor first."
                    ),
                }
            ],
            "created": "2025-02-03T08:27:49.297997+00:00",
        },
    }
    await client.send_json_auto_id({"type": "supervisor/event", "data": event})
    response = await client.receive_json()
    assert response["success"]

    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "restore_backup",
        "reason": "backup_reader_writer_error",
        "stage": None,
        "state": "failed",
    }

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}

    response = await client.receive_json()
    assert not response["success"]
    assert response["error"] == {
        "code": "home_assistant_error",
        "message": (
            "Restore failed: [{'type': 'BackupInvalidError', 'message': \"Backup "
            "was made on supervisor version 2025.02.2.dev3105, can't restore on "
            '2025.01.2.dev3105. Must update supervisor first."}]'
        ),
    }