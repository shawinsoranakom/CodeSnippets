async def test_reader_writer_create_download_remove_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
    exception: Exception,
    method: str,
    download_call_count: int,
    remove_call_count: int,
    expected_events_before_failed: list[dict[str, str]],
) -> None:
    """Test download and remove error when generating a backup."""
    client = await hass_ws_client(hass)
    supervisor_client.backups.partial_backup.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.backup_info.return_value = TEST_BACKUP_DETAILS_5
    supervisor_client.jobs.get_job.return_value = TEST_JOB_NOT_DONE
    method_mock = getattr(supervisor_client.backups, method)
    method_mock.side_effect = exception

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
        "reason": None,
        "stage": "upload_to_agents",
        "state": "in_progress",
    }

    # Consume any upload progress events before the final state event
    response = await client.receive_json()
    while "uploaded_bytes" in response["event"]:
        response = await client.receive_json()
    for expected_event in expected_events_before_failed:
        assert response["event"] == expected_event
        response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "create_backup",
        "reason": "upload_failed",
        "stage": None,
        "state": "failed",
    }

    await hass.async_block_till_done()

    assert supervisor_client.backups.backup_info.call_count == 1
    assert supervisor_client.backups.download_backup.call_count == download_call_count
    assert supervisor_client.backups.remove_backup.call_count == remove_call_count

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}