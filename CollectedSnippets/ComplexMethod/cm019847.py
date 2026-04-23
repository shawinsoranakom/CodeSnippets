async def test_initiate_backup_file_error_create_backup(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    generate_backup_id: MagicMock,
    caplog: pytest.LogCaptureFixture,
    mkdir_call_count: int,
    mkdir_exception: Exception | None,
    atomic_contents_add_call_count: int,
    atomic_contents_add_exception: Exception | None,
    stat_call_count: int,
    stat_exception: Exception | None,
    error_message: str,
) -> None:
    """Test file error during generate backup, while creating backup."""
    agent_ids = ["test.remote"]

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

    await ws_client.send_json_auto_id({"type": "backup/subscribe_events"})

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    result = await ws_client.receive_json()
    assert result["success"] is True

    with (
        patch(
            "homeassistant.components.backup.manager.atomic_contents_add",
            side_effect=atomic_contents_add_exception,
        ) as atomic_contents_add_mock,
        patch("pathlib.Path.mkdir", side_effect=mkdir_exception) as mkdir_mock,
        patch("pathlib.Path.stat", side_effect=stat_exception) as stat_mock,
    ):
        await ws_client.send_json_auto_id(
            {"type": "backup/generate", "agent_ids": agent_ids}
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
        "reason": "upload_failed",
        "stage": None,
        "state": CreateBackupState.FAILED,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    assert atomic_contents_add_mock.call_count == atomic_contents_add_call_count
    assert mkdir_mock.call_count == mkdir_call_count
    assert stat_mock.call_count == stat_call_count

    assert error_message in caplog.text