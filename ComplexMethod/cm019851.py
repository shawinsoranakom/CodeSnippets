async def test_receive_backup_non_agent_upload_error(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
    exception: Exception,
) -> None:
    """Test non agent upload error during backup receive."""
    mock_agents = await setup_backup_integration(hass, remote_agents=["test.remote"])

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
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    assert DOMAIN not in hass_storage
    assert resp.status == 500
    assert open_mock.call_count == 1
    assert move_mock.call_count == 0
    assert unlink_mock.call_count == 0