async def test_reader_writer_create_report_progress(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    supervisor_client: AsyncMock,
) -> None:
    """Test generating a backup."""
    client = await hass_ws_client(hass)
    freezer.move_to("2025-01-30 13:42:12.345678")
    supervisor_client.backups.partial_backup.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.backup_info.return_value = TEST_BACKUP_DETAILS
    supervisor_client.jobs.get_job.return_value = TEST_JOB_NOT_DONE

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {"type": "backup/generate", "agent_ids": ["hassio.local"], "name": "Test"}
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
        DEFAULT_BACKUP_OPTIONS
    )

    supervisor_event_base = {"uuid": TEST_JOB_ID, "reference": "test_slug"}
    supervisor_events = [
        supervisor_event_base | {"done": False, "stage": "addon_repositories"},
        supervisor_event_base | {"done": False, "stage": None},  # Will be skipped
        supervisor_event_base | {"done": False, "stage": "unknown"},  # Will be skipped
        supervisor_event_base | {"done": False, "stage": "home_assistant"},
        supervisor_event_base | {"done": False, "stage": "addons"},
        supervisor_event_base | {"done": True, "stage": "finishing_file"},
    ]
    expected_manager_events = [
        "addon_repositories",
        "home_assistant",
        "addons",
        "finishing_file",
    ]

    for supervisor_event in supervisor_events:
        await client.send_json_auto_id(
            {
                "type": "supervisor/event",
                "data": {"event": "job", "data": supervisor_event},
            }
        )

    acks = 0
    events = []
    for _ in range(len(supervisor_events) + len(expected_manager_events)):
        response = await client.receive_json()
        if "event" in response:
            events.append(response)
            continue
        assert response["success"]
        acks += 1

    assert acks == len(supervisor_events)
    assert len(events) == len(expected_manager_events)

    for i, event in enumerate(events):
        assert event["event"] == {
            "manager_state": "create_backup",
            "reason": None,
            "stage": expected_manager_events[i],
            "state": "in_progress",
        }

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