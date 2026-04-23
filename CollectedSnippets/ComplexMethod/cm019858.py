async def test_restore_backup_agent_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    exception: Exception,
    error_code: str,
    error_message: str,
    expected_reason: str,
) -> None:
    """Test restore backup with agent error."""
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

    mock_agents["test.remote"].async_download_backup.side_effect = exception
    with (
        patch("pathlib.Path.open"),
        patch("pathlib.Path.write_text") as mocked_write_text,
        patch("homeassistant.core.ServiceRegistry.async_call") as mocked_service_call,
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
            "reason": expected_reason,
            "stage": None,
            "state": RestoreBackupState.FAILED,
        }

        result = await ws_client.receive_json()
        assert result["event"] == {"manager_state": BackupManagerState.IDLE}

        result = await ws_client.receive_json()
        assert not result["success"]
        assert result["error"]["code"] == error_code
        assert result["error"]["message"] == error_message

    assert mock_agents["test.remote"].async_download_backup.call_count == 1
    assert mocked_write_text.call_count == 0
    assert mocked_service_call.call_count == 0