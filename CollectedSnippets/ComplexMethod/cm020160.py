async def test_reader_writer_create_addon_folder_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    supervisor_client: AsyncMock,
    addon_info_side_effect: list[Any],
) -> None:
    """Test generating a backup."""
    addon_info_side_effect[0].name = "Advanced SSH & Web Terminal"
    assert dt.datetime.__name__ == "HAFakeDatetime"
    assert dt.HAFakeDatetime.__name__ == "HAFakeDatetime"
    client = await hass_ws_client(hass)
    freezer.move_to("2025-01-30 13:42:12.345678")
    supervisor_client.backups.partial_backup.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.backup_info.return_value = TEST_BACKUP_DETAILS
    supervisor_client.jobs.get_job.side_effect = [
        TEST_JOB_NOT_DONE,
        supervisor_jobs.Job.from_dict(
            (
                await async_load_json_object_fixture(
                    hass, "backup_done_with_addon_folder_errors.json", DOMAIN
                )
            )["data"]
        ),
    ]

    issue_registry = ir.async_get(hass)
    assert not issue_registry.issues

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {
            "type": "backup/config/update",
            "create_backup": {
                "agent_ids": ["hassio.local"],
                "include_addons": ["core_ssh", "core_whisper"],
                "include_all_addons": False,
                "include_database": True,
                "include_folders": ["media", "share"],
                "name": "Test",
            },
        }
    )
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id({"type": "backup/generate_with_automatic_settings"})
    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "create_backup",
        "reason": None,
        "stage": None,
        "state": "in_progress",
    }

    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {"backup_job_id": TEST_JOB_ID}

    supervisor_client.backups.partial_backup.assert_called_once_with(
        replace(
            DEFAULT_BACKUP_OPTIONS,
            addons={"core_ssh", "core_whisper"},
            extra=DEFAULT_BACKUP_OPTIONS.extra | {"with_automatic_settings": True},
            folders={Folder.MEDIA, Folder.SHARE, Folder.SSL},
        )
    )

    await client.send_json_auto_id(
        {
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {"done": True, "uuid": TEST_JOB_ID, "reference": "test_slug"},
            },
        }
    )
    response = await client.receive_json()
    assert response["success"]

    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "create_backup",
        "reason": None,
        "stage": "upload_to_agents",
        "state": "in_progress",
    }

    # Consume any upload progress events before the final state event
    response = await client.receive_json()
    while "uploaded_bytes" in response["event"]:
        response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "create_backup",
        "reason": None,
        "stage": "cleaning_up",
        "state": "in_progress",
    }

    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "create_backup",
        "reason": None,
        "stage": None,
        "state": "completed",
    }

    supervisor_client.backups.download_backup.assert_not_called()
    supervisor_client.backups.remove_backup.assert_not_called()

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}

    # Check that the expected issue was created
    assert list(issue_registry.issues) == [("backup", "automatic_backup_failed")]
    issue = issue_registry.issues[("backup", "automatic_backup_failed")]
    assert issue.translation_key == "automatic_backup_failed_agents_addons_folders"
    assert issue.translation_placeholders == {
        "failed_addons": "Advanced SSH & Web Terminal, core_whisper",
        "failed_agents": "-",
        "failed_folders": "share, ssl, media",
    }