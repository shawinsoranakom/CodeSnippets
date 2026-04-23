async def test_initiate_backup_non_agent_upload_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    generate_backup_id: MagicMock,
    hass_storage: dict[str, Any],
    exception: Exception,
) -> None:
    """Test an unknown or writer upload error during backup generation."""
    agent_ids = [LOCAL_AGENT_ID, "test.remote"]
    mock_agents = await setup_backup_integration(hass, remote_agents=["test.remote"])

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

    mock_agents["test.remote"].async_upload_backup.side_effect = exception
    with patch("pathlib.Path.open", mock_open(read_data=b"test")):
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
        "reason": "upload_failed",
        "stage": None,
        "state": CreateBackupState.FAILED,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    assert DOMAIN not in hass_storage