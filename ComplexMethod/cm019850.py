async def test_receive_backup_agent_error(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
    exception: Exception,
) -> None:
    """Test upload error during backup receive."""
    backup_1 = replace(TEST_BACKUP_ABC123, backup_id="backup1")  # matching instance id
    backup_2 = replace(TEST_BACKUP_DEF456, backup_id="backup2")  # other instance id
    backup_3 = replace(TEST_BACKUP_ABC123, backup_id="backup3")  # matching instance id
    backups_info: list[dict[str, Any]] = [
        {
            "addons": [
                {
                    "name": "Test",
                    "slug": "test",
                    "version": "1.0.0",
                },
            ],
            "agents": {"test.remote": {"protected": False, "size": 0}},
            "backup_id": "backup1",
            "database_included": True,
            "date": "1970-01-01T00:00:00.000Z",
            "extra_metadata": {
                "instance_id": "our_uuid",
                "with_automatic_settings": True,
            },
            "failed_addons": [],
            "failed_agent_ids": [],
            "failed_folders": [],
            "folders": [
                "media",
                "share",
            ],
            "homeassistant_included": True,
            "homeassistant_version": "2024.12.0",
            "name": "Test",
            "with_automatic_settings": True,
        },
        {
            "addons": [],
            "agents": {"test.remote": {"protected": False, "size": 1}},
            "backup_id": "backup2",
            "database_included": False,
            "date": "1980-01-01T00:00:00.000Z",
            "extra_metadata": {
                "instance_id": "unknown_uuid",
                "with_automatic_settings": True,
            },
            "failed_addons": [],
            "failed_agent_ids": [],
            "failed_folders": [],
            "folders": [
                "media",
                "share",
            ],
            "homeassistant_included": True,
            "homeassistant_version": "2024.12.0",
            "name": "Test 2",
            "with_automatic_settings": None,
        },
        {
            "addons": [
                {
                    "name": "Test",
                    "slug": "test",
                    "version": "1.0.0",
                },
            ],
            "agents": {"test.remote": {"protected": False, "size": 0}},
            "backup_id": "backup3",
            "database_included": True,
            "date": "1970-01-01T00:00:00.000Z",
            "extra_metadata": {
                "instance_id": "our_uuid",
                "with_automatic_settings": True,
            },
            "failed_addons": [],
            "failed_agent_ids": [],
            "failed_folders": [],
            "folders": [
                "media",
                "share",
            ],
            "homeassistant_included": True,
            "homeassistant_version": "2024.12.0",
            "name": "Test",
            "with_automatic_settings": True,
        },
    ]

    mock_agents = await setup_backup_integration(
        hass,
        remote_agents=["test.remote"],
        backups={"test.remote": [backup_1, backup_2, backup_3]},
    )

    client = await hass_client()
    ws_client = await hass_ws_client(hass)

    await ws_client.send_json_auto_id({"type": "backup/info"})
    result = await ws_client.receive_json()

    assert result["success"] is True
    assert result["result"] == {
        "backups": backups_info,
        "agent_errors": {},
        "last_attempted_automatic_backup": None,
        "last_completed_automatic_backup": None,
        "last_action_event": None,
        "next_automatic_backup": None,
        "next_automatic_backup_additional": False,
        "state": "idle",
    }

    await ws_client.send_json_auto_id(
        {"type": "backup/config/update", "retention": {"copies": 1, "days": None}}
    )
    result = await ws_client.receive_json()
    assert result["success"]

    await ws_client.send_json_auto_id({"type": "backup/subscribe_events"})

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    result = await ws_client.receive_json()
    assert result["success"] is True

    upload_data = "test"
    open_mock = mock_open(read_data=upload_data.encode(encoding="utf-8"))

    mock_agents["test.remote"].async_upload_backup.side_effect = exception
    with (
        patch("pathlib.Path.open", open_mock),
        patch("shutil.move") as move_mock,
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=TEST_BACKUP_ABC123,
        ),
        patch("pathlib.Path.unlink") as unlink_mock,
    ):
        resp = await client.post(
            "/api/backup/upload?agent_id=test.remote",
            data={"file": StringIO(upload_data)},
        )
        await hass.async_block_till_done()

    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.RECEIVE_BACKUP,
        "reason": None,
        "stage": None,
        "state": ReceiveBackupState.IN_PROGRESS,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.RECEIVE_BACKUP,
        "reason": None,
        "stage": ReceiveBackupStage.RECEIVE_FILE,
        "state": ReceiveBackupState.IN_PROGRESS,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.RECEIVE_BACKUP,
        "reason": None,
        "stage": ReceiveBackupStage.UPLOAD_TO_AGENTS,
        "state": ReceiveBackupState.IN_PROGRESS,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.RECEIVE_BACKUP,
        "reason": None,
        "stage": None,
        "state": ReceiveBackupState.COMPLETED,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    await ws_client.send_json_auto_id({"type": "backup/info"})
    result = await ws_client.receive_json()

    assert result["success"] is True
    assert result["result"] == {
        "backups": backups_info,
        "agent_errors": {},
        "last_attempted_automatic_backup": None,
        "last_completed_automatic_backup": None,
        "last_action_event": {
            "manager_state": "receive_backup",
            "reason": None,
            "stage": None,
            "state": "completed",
        },
        "next_automatic_backup": None,
        "next_automatic_backup_additional": False,
        "state": "idle",
    }

    await hass.async_block_till_done()
    assert hass_storage[DOMAIN]["data"]["backups"] == [
        {
            "backup_id": "abc123",
            "failed_addons": [],
            "failed_agent_ids": ["test.remote"],
            "failed_folders": [],
        }
    ]

    assert resp.status == 201
    assert open_mock.call_count == 1
    assert move_mock.call_count == 0
    assert unlink_mock.call_count == 1
    assert mock_agents["test.remote"].async_delete_backup.call_count == 0