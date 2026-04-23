async def test_reader_writer_create_remote_backup(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    supervisor_client: AsyncMock,
) -> None:
    """Test generating a backup which will be uploaded to a remote agent."""
    client = await hass_ws_client(hass)
    freezer.move_to("2025-01-30 13:42:12.345678")
    supervisor_client.backups.partial_backup.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.backup_info.return_value = TEST_BACKUP_DETAILS_5
    supervisor_client.jobs.get_job.return_value = TEST_JOB_NOT_DONE

    remote_agent = mock_backup_agent("remote")
    await _setup_backup_platform(
        hass,
        domain="test",
        platform=Mock(
            async_get_backup_agents=AsyncMock(return_value=[remote_agent]),
            spec_set=BackupAgentPlatformProtocol,
        ),
    )

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {"type": "backup/generate", "agent_ids": ["test.remote"], "name": "Test"}
    )
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
        replace(DEFAULT_BACKUP_OPTIONS, location=[LOCATION_CLOUD_BACKUP]),
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

    supervisor_client.backups.download_backup.assert_called_once_with("test_slug")
    supervisor_client.backups.remove_backup.assert_called_once_with(
        "test_slug",
        options=supervisor_backups.RemoveBackupOptions({LOCATION_CLOUD_BACKUP}),
    )