async def test_reader_writer_restore_remote_backup(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
) -> None:
    """Test restoring a backup from a remote agent."""
    client = await hass_ws_client(hass)
    supervisor_client.backups.partial_restore.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.list.return_value = [TEST_BACKUP_5]
    supervisor_client.backups.backup_info.return_value = TEST_BACKUP_DETAILS_5
    supervisor_client.jobs.get_job.return_value = TEST_JOB_NOT_DONE

    backup_id = "abc123"
    test_backup = AgentBackup(
        addons=[AddonInfo(name="Test", slug="test", version="1.0.0")],
        backup_id=backup_id,
        database_included=True,
        date="1970-01-01T00:00:00.000Z",
        extra_metadata={},
        folders=[Folder.MEDIA, Folder.SHARE],
        homeassistant_included=True,
        homeassistant_version="2024.12.0",
        name="Test",
        protected=False,
        size=0,
    )
    remote_agent = mock_backup_agent("remote", backups=[test_backup])
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
    assert response["event"] == {
        "manager_state": "idle",
    }
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {"type": "backup/restore", "agent_id": "test.remote", "backup_id": backup_id}
    )
    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "restore_backup",
        "reason": None,
        "stage": None,
        "state": "in_progress",
    }

    remote_agent.async_download_backup.assert_called_once_with(backup_id)
    assert len(remote_agent.async_get_backup.mock_calls) == 2
    for call in remote_agent.async_get_backup.mock_calls:
        assert call.args[0] == backup_id
    supervisor_client.backups.partial_restore.assert_called_once_with(
        backup_id,
        supervisor_backups.PartialRestoreOptions(
            addons=None,
            background=True,
            folders=None,
            homeassistant=True,
            location=LOCATION_CLOUD_BACKUP,
            password=None,
        ),
    )

    await client.send_json_auto_id(
        {
            "type": "supervisor/event",
            "data": {"event": "job", "data": {"done": True, "uuid": TEST_JOB_ID}},
        }
    )
    response = await client.receive_json()
    assert response["success"]

    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "restore_backup",
        "reason": None,
        "stage": None,
        "state": "completed",
    }

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}

    response = await client.receive_json()
    assert response["success"]
    assert response["result"] is None