async def test_restore_backup(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    agent_id: str,
    backup_id: str,
    password_param: dict[str, str],
    backup_path: Path,
    restore_database: bool,
    restore_homeassistant: bool,
    dir: str,
) -> None:
    """Test restore backup."""
    password = password_param.get("password")
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
        await ws_client.send_json_auto_id(
            {
                "type": "backup/restore",
                "backup_id": backup_id,
                "agent_id": agent_id,
                "restore_database": restore_database,
                "restore_homeassistant": restore_homeassistant,
            }
            | password_param
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
            "reason": None,
            "stage": None,
            "state": RestoreBackupState.CORE_RESTART,
        }

        # Note: The core restart is not tested here, in reality the following events
        # are not sent because the core restart closes the WS connection.
        result = await ws_client.receive_json()
        assert result["event"] == {
            "manager_state": BackupManagerState.RESTORE_BACKUP,
            "reason": None,
            "stage": None,
            "state": RestoreBackupState.COMPLETED,
        }

        result = await ws_client.receive_json()
        assert result["event"] == {"manager_state": BackupManagerState.IDLE}

        result = await ws_client.receive_json()
        assert result["success"] is True

    full_backup_path = f"{hass.config.path()}/{dir}/{backup_path.name}"
    expected_restore_file = json.dumps(
        {
            "path": full_backup_path,
            "password": password,
            "remove_after_restore": agent_id != LOCAL_AGENT_ID,
            "restore_database": restore_database,
            "restore_homeassistant": restore_homeassistant,
        }
    )
    validate_password_mock.assert_called_once_with(Path(full_backup_path), password)
    assert mocked_write_text.call_args[0][0] == expected_restore_file
    assert mocked_service_call.called