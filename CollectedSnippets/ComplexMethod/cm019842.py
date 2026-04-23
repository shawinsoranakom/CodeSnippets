async def test_initiate_backup(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    mocked_json_bytes: Mock,
    generate_backup_id: MagicMock,
    params: dict[str, Any],
    agent_ids: list[str],
    backup_directory: str,
    name: str | None,
    expected_name: str,
    expected_filename: str,
    expected_agent_ids: list[str],
    expected_failed_agent_ids: list[str],
    temp_file_unlink_call_count: int,
) -> None:
    """Test generate backup."""
    await setup_backup_integration(hass, remote_agents=["test.remote"])

    ws_client = await hass_ws_client(hass)
    freezer.move_to("2025-01-30 13:42:12.345678")

    include_database = params.get("include_database", True)
    password = params.get("password")

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

    with (
        patch("pathlib.Path.open", mock_open(read_data=b"test")),
        patch("pathlib.Path.unlink") as unlink_mock,
    ):
        await ws_client.send_json_auto_id(
            {"type": "backup/generate", "agent_ids": agent_ids, "name": name} | params
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
        "reason": None,
        "stage": CreateBackupStage.CLEANING_UP,
        "state": CreateBackupState.IN_PROGRESS,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {
        "manager_state": BackupManagerState.CREATE_BACKUP,
        "reason": None,
        "stage": None,
        "state": CreateBackupState.COMPLETED,
    }

    result = await ws_client.receive_json()
    assert result["event"] == {"manager_state": BackupManagerState.IDLE}

    assert unlink_mock.call_count == temp_file_unlink_call_count

    assert mocked_json_bytes.call_count == 1
    backup_json_dict = mocked_json_bytes.call_args[0][0]
    assert isinstance(backup_json_dict, dict)
    assert backup_json_dict == {
        "compressed": True,
        "date": ANY,
        "extra": {
            "instance_id": "our_uuid",
            "with_automatic_settings": False,
        },
        "homeassistant": {
            "exclude_database": not include_database,
            "version": "2025.1.0",
        },
        "name": expected_name,
        "protected": bool(password),
        "slug": backup_id,
        "type": "partial",
        "version": 2,
    }

    await ws_client.send_json_auto_id(
        {"type": "backup/details", "backup_id": backup_id}
    )
    result = await ws_client.receive_json()

    backup_data = result["result"]["backup"]

    assert backup_data == {
        "addons": [],
        "agents": {
            agent_id: {"protected": bool(password), "size": ANY}
            for agent_id in expected_agent_ids
        },
        "backup_id": backup_id,
        "database_included": include_database,
        "date": ANY,
        "extra_metadata": {"instance_id": "our_uuid", "with_automatic_settings": False},
        "failed_addons": [],
        "failed_agent_ids": expected_failed_agent_ids,
        "failed_folders": [],
        "folders": [],
        "homeassistant_included": True,
        "homeassistant_version": "2025.1.0",
        "name": expected_name,
        "with_automatic_settings": False,
    }

    expected_files = {
        f"data/{file}" for file in _EXPECTED_FILES_WITH_DATABASE[include_database]
    }
    expected_files.add("data")

    with tarfile.TarFile(
        hass.config.path(f"{backup_directory}/{expected_filename}"), mode="r"
    ) as outer_tar:
        core_tar_io = outer_tar.extractfile("homeassistant.tar.gz")
        assert core_tar_io is not None
        with SecureTarFile(
            fileobj=core_tar_io,
            gzip=True,
            password=password,
        ) as core_tar:
            assert set(core_tar.getnames()) == expected_files