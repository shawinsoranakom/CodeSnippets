async def test_initiate_backup_with_task_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    generate_backup_id: MagicMock,
    create_backup: AsyncMock,
    exception: Exception,
) -> None:
    """Test backup task error during backup generation."""
    backup_task: asyncio.Future[Any] = asyncio.Future()
    backup_task.set_exception(exception)
    create_backup.return_value = (NewBackup(backup_job_id="abc123"), backup_task)
    agent_ids = [LOCAL_AGENT_ID, "test.remote"]

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

    await ws_client.send_json_auto_id(
        {"type": "backup/generate", "agent_ids": agent_ids}
    )
    await hass.async_block_till_done()

    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.CREATE_BACKUP,
        "reason": None,
        "stage": None,
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

    result = await ws_client.receive_json()
    assert result["success"] is True

    backup_id = result["result"]["backup_job_id"]
    assert backup_id == generate_backup_id.return_value