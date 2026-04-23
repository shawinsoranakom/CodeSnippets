async def test_receive_backup_file_write_error(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    open_call_count: int,
    open_exception: Exception | None,
    write_call_count: int,
    write_exception: Exception | None,
    close_call_count: int,
    close_exception: Exception | None,
) -> None:
    """Test file write error during backup receive."""
    await setup_backup_integration(hass, remote_agents=["test.remote"])

    client = await hass_client()
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

    upload_data = "test"
    open_mock = mock_open(read_data=upload_data.encode(encoding="utf-8"))
    open_mock.side_effect = open_exception
    open_mock.return_value.write.side_effect = write_exception
    open_mock.return_value.close.side_effect = close_exception

    with (
        patch("pathlib.Path.open", open_mock),
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
        "reason": "unknown_error",
        "stage": None,
        "state": ReceiveBackupState.FAILED,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    assert resp.status == 500
    assert open_mock.call_count == open_call_count
    assert open_mock.return_value.write.call_count == write_call_count
    assert open_mock.return_value.close.call_count == close_call_count