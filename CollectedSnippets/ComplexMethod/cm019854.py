async def test_receive_backup_file_read_error(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    open_call_count: int,
    open_exception: list[Exception | None],
    read_call_count: int,
    read_exception: Exception | None,
    close_call_count: int,
    close_exception: list[Exception | None],
    unlink_call_count: int,
    unlink_exception: Exception | None,
    final_state: ReceiveBackupState,
    final_state_reason: str | None,
    response_status: int,
) -> None:
    """Test file read error during backup receive."""
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
    open_mock.return_value.read.side_effect = read_exception
    open_mock.return_value.close.side_effect = close_exception

    with (
        patch("pathlib.Path.open", open_mock),
        patch("pathlib.Path.unlink", side_effect=unlink_exception) as unlink_mock,
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=TEST_BACKUP_ABC123,
        ),
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

    # Consume any upload progress events before the final state event
    result = await ws_client.receive_json()
    while "uploaded_bytes" in result["event"]:
        result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.RECEIVE_BACKUP,
        "reason": final_state_reason,
        "stage": None,
        "state": final_state,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    assert resp.status == response_status
    assert open_mock.call_count == open_call_count
    assert open_mock.return_value.read.call_count == read_call_count
    assert open_mock.return_value.close.call_count == close_call_count
    assert unlink_mock.call_count == unlink_call_count