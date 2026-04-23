async def test_initiate_backup_per_agent_encryption(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    generate_backup_id: MagicMock,
    commands: dict[str, Any],
    agent_ids: list[str],
    password: str | None,
    protected_backup: dict[str, bool],
    inner_tar_password: str | None,
) -> None:
    """Test generate backup where encryption is selectively set on agents."""
    await setup_backup_integration(hass, remote_agents=["test.remote"])

    ws_client = await hass_ws_client(hass)

    await ws_client.send_json_auto_id({"type": "backup/info"})
    result = await ws_client.receive_json()
    assert result["success"] is True
    assert result["result"] == {
        "backups": [],
        "agent_errors": {},
        "last_attempted_automatic_backup": None,
        "last_completed_automatic_backup": None,
        "last_action_event": None,
        "next_automatic_backup": None,
        "next_automatic_backup_additional": False,
        "state": "idle",
    }

    for command in commands:
        await ws_client.send_json_auto_id(command)
        result = await ws_client.receive_json()
        assert result["success"] is True

    await ws_client.send_json_auto_id({"type": "backup/subscribe_events"})

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    result = await ws_client.receive_json()
    assert result["success"] is True

    with (
        patch("pathlib.Path.open", mock_open(read_data=b"test")),
        patch(
            "securetar.SecureTarArchive.__init__",
            autospec=True,
            wraps=SecureTarArchive.__init__,
        ) as mock_secure_tar_archive,
    ):
        await ws_client.send_json_auto_id(
            {
                "type": "backup/generate",
                "agent_ids": agent_ids,
                "password": password,
                "name": "test",
            }
        )
        result = await ws_client.receive_json()
        assert result["event"] == {
            "manager_state": BackupManagerState.CREATE_BACKUP,
            "reason": None,
            "stage": None,
            "state": CreateBackupState.IN_PROGRESS,
        }
        result = await ws_client.receive_json()
        assert result["success"] is True

        backup_id = result["result"]["backup_job_id"]
        assert backup_id == generate_backup_id.return_value

        await hass.async_block_till_done()

    assert mock_secure_tar_archive.mock_calls[0] == call(
        ANY, ANY, "w", bufsize=4194304, create_version=3, password=inner_tar_password
    )

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
        "reason": None,
        "stage": None,
        "state": CreateBackupState.COMPLETED,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    await ws_client.send_json_auto_id(
        {"type": "backup/details", "backup_id": backup_id}
    )
    result = await ws_client.receive_json()

    backup_data = result["result"]["backup"]

    assert backup_data == {
        "addons": [],
        "agents": {
            agent_id: {"protected": protected_backup[agent_id], "size": ANY}
            for agent_id in agent_ids
        },
        "backup_id": backup_id,
        "database_included": True,
        "date": ANY,
        "extra_metadata": {"instance_id": "our_uuid", "with_automatic_settings": False},
        "failed_addons": [],
        "failed_agent_ids": [],
        "failed_folders": [],
        "folders": [],
        "homeassistant_included": True,
        "homeassistant_version": "2025.1.0",
        "name": "test",
        "with_automatic_settings": False,
    }