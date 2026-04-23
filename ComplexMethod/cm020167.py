async def test_reader_writer_create_info_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
    exception: Exception,
) -> None:
    """Test backup info error when generating a backup."""
    client = await hass_ws_client(hass)
    supervisor_client.backups.partial_backup.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.backup_info.side_effect = exception
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

    assert supervisor_client.backups.partial_backup.call_count == 1

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
        "reason": "upload_failed",
        "stage": None,
        "state": "failed",
    }

    await hass.async_block_till_done()

    assert supervisor_client.backups.backup_info.call_count == 1
    assert supervisor_client.backups.download_backup.call_count == 0
    assert supervisor_client.backups.remove_backup.call_count == 0

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}