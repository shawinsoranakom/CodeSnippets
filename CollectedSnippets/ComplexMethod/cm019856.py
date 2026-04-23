async def test_restore_backup_wrong_password(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    agent_id: str,
    dir: str,
) -> None:
    """Test restore backup wrong password."""
    password = "hunter2"
    await setup_backup_integration(
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

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.open"),
        patch("pathlib.Path.write_text") as mocked_write_text,
        patch("homeassistant.core.ServiceRegistry.async_call") as mocked_service_call,
        patch(
            "homeassistant.components.backup.manager.validate_password"
        ) as validate_password_mock,
        patch(
            "homeassistant.components.backup.backup.read_backup",
            side_effect=mock_read_backup,
        ),
    ):
        validate_password_mock.return_value = False
        await ws_client.send_json_auto_id(
            {
                "type": "backup/restore",
                "backup_id": TEST_BACKUP_ABC123.backup_id,
                "agent_id": agent_id,
                "password": password,
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
            "reason": "password_incorrect",
            "stage": None,
            "state": RestoreBackupState.FAILED,
        }

        result = await ws_client.receive_json()
        assert result["event"] == {"manager_state": BackupManagerState.IDLE}

        result = await ws_client.receive_json()
        assert not result["success"]
        assert result["error"]["code"] == "password_incorrect"

    backup_path = f"{hass.config.path()}/{dir}/abc123.tar"
    validate_password_mock.assert_called_once_with(Path(backup_path), password)
    mocked_write_text.assert_not_called()
    mocked_service_call.assert_not_called()