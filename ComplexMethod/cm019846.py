async def test_initiate_backup_file_error_upload_to_agents(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    generate_backup_id: MagicMock,
    open_call_count: int,
    open_exception: Exception | None,
    read_call_count: int,
    read_exception: Exception | None,
    close_call_count: int,
    close_exception: Exception | None,
    unlink_call_count: int,
    unlink_exception: Exception | None,
) -> None:
    """Test file error during generate backup, while uploading to agents."""
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

    open_mock = mock_open(read_data=b"test")
    open_mock.side_effect = open_exception
    open_mock.return_value.read.side_effect = read_exception
    open_mock.return_value.close.side_effect = close_exception

    with (
        patch("pathlib.Path.open", open_mock),
        patch("pathlib.Path.unlink", side_effect=unlink_exception) as unlink_mock,
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

    assert open_mock.call_count == open_call_count
    assert open_mock.return_value.read.call_count == read_call_count
    assert open_mock.return_value.close.call_count == close_call_count
    assert unlink_mock.call_count == unlink_call_count