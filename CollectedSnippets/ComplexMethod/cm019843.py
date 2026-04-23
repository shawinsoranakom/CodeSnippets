async def test_initiate_backup_with_agent_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    generate_backup_id: MagicMock,
    hass_storage: dict[str, Any],
    exception: Exception,
) -> None:
    """Test agent upload error during backup generation."""
    agent_ids = [LOCAL_AGENT_ID, "test.remote"]
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

    mock_agents["test.remote"].async_upload_backup.side_effect = exception
    with patch("pathlib.Path.open", mock_open(read_data=b"test")):
        await ws_client.send_json_auto_id(
            {"type": "backup/generate", "agent_ids": agent_ids}
        )
        result = await ws_client.receive_json()
        assert result["event"] == {
            "manager_state": BackupManagerState.CREATE_BACKUP,
            "stage": None,
            "reason": None,
            "state": CreateBackupState.IN_PROGRESS,
        }
        result = await ws_client.receive_json()
        assert result["success"] is True

        backup_id = result["result"]["backup_job_id"]
        assert backup_id == generate_backup_id.return_value

        await hass.async_block_till_done()

    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.CREATE_BACKUP,
        "reason": None,
        "stage": CreateBackupStage.HOME_ASSISTANT,
        "state": CreateBackupState.IN_PROGRESS,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.CREATE_BACKUP,
        "reason": None,
        "stage": CreateBackupStage.UPLOAD_TO_AGENTS,
        "state": CreateBackupState.IN_PROGRESS,
    }

    # Consume any upload progress events before the final state event
    result = await ws_client.receive_json()
    while "uploaded_bytes" in result["event"]:
        result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.CREATE_BACKUP,
        "reason": None,
        "stage": CreateBackupStage.CLEANING_UP,
        "state": CreateBackupState.IN_PROGRESS,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.CREATE_BACKUP,
        "reason": "upload_failed",
        "stage": None,
        "state": CreateBackupState.FAILED,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    new_expected_backup_data = {
        "addons": [],
        "agents": {"backup.local": {"protected": False, "size": 10240}},
        "backup_id": "abc123",
        "database_included": True,
        "date": ANY,
        "extra_metadata": {"instance_id": "our_uuid", "with_automatic_settings": False},
        "failed_addons": [],
        "failed_agent_ids": ["test.remote"],
        "failed_folders": [],
        "folders": [],
        "homeassistant_included": True,
        "homeassistant_version": "2025.1.0",
        "name": "Custom backup 2025.1.0",
        "with_automatic_settings": False,
    }

    await ws_client.send_json_auto_id({"type": "backup/info"})
    result = await ws_client.receive_json()
    backups_response = result["result"].pop("backups")

    assert len(backups_response) == 4
    assert new_expected_backup_data in backups_response
    assert result["result"] == {
        "agent_errors": {},
        "last_attempted_automatic_backup": None,
        "last_completed_automatic_backup": None,
        "last_action_event": {
            "manager_state": "create_backup",
            "reason": "upload_failed",
            "stage": None,
            "state": "failed",
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

    # one of the two matching backups with the remote agent should have been deleted
    assert mock_agents["test.remote"].async_delete_backup.call_count == 1