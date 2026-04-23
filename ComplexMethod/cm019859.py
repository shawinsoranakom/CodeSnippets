async def test_restore_backup_file_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    open_call_count: int,
    open_exception: list[Exception | None],
    write_call_count: int,
    write_exception: Exception | None,
    close_call_count: int,
    close_exception: list[Exception | None],
    write_text_call_count: int,
    write_text_exception: Exception | None,
    validate_password_call_count: int,
) -> None:
    """Test restore backup with file error."""
    mock_agents = await setup_backup_integration(
        hass,
        remote_agents=["test.remote"],
        backups={"test.remote": [TEST_BACKUP_ABC123]},
    )
    ws_client = await hass_ws_client(hass)

    await ws_client.send_json_auto_id({"type": "backup/subscribe_events"})

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    result = await ws_client.receive_json()
    assert result["success"] is True

    open_mock = mock_open()
    open_mock.side_effect = open_exception
    open_mock.return_value.write.side_effect = write_exception
    open_mock.return_value.close.side_effect = close_exception

    with (
        patch("pathlib.Path.open", open_mock),
        patch(
            "pathlib.Path.write_text", side_effect=write_text_exception
        ) as mocked_write_text,
        patch("homeassistant.core.ServiceRegistry.async_call") as mocked_service_call,
        patch(
            "homeassistant.components.backup.manager.validate_password"
        ) as validate_password_mock,
    ):
        await ws_client.send_json_auto_id(
            {
                "type": "backup/restore",
                "backup_id": TEST_BACKUP_ABC123.backup_id,
                "agent_id": "test.remote",
            }
        )

        result = await ws_client.receive_json()
        assert result["event"] == {
            "manager_state": BackupManagerState.RESTORE_BACKUP,
            "reason": None,
            "stage": None,
            "state": RestoreBackupState.IN_PROGRESS,
        }

        result = await ws_client.receive_json()
        assert result["event"] == {
            "manager_state": BackupManagerState.RESTORE_BACKUP,
            "reason": "unknown_error",
            "stage": None,
            "state": RestoreBackupState.FAILED,
        }

        result = await ws_client.receive_json()
        assert result["event"] == {"manager_state": BackupManagerState.IDLE}

        result = await ws_client.receive_json()
        assert not result["success"]
        assert result["error"]["code"] == "unknown_error"
        assert result["error"]["message"] == "Unknown error"

    assert mock_agents["test.remote"].async_download_backup.call_count == 1
    assert validate_password_mock.call_count == validate_password_call_count
    assert open_mock.call_count == open_call_count
    assert open_mock.return_value.write.call_count == write_call_count
    assert open_mock.return_value.close.call_count == close_call_count
    assert mocked_write_text.call_count == write_text_call_count
    assert mocked_service_call.call_count == 0