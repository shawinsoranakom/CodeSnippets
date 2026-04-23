async def test_reader_writer_restore_report_progress(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
) -> None:
    """Test restoring a backup."""
    client = await hass_ws_client(hass)
    supervisor_client.backups.partial_restore.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.list.return_value = [TEST_BACKUP]
    supervisor_client.backups.backup_info.return_value = TEST_BACKUP_DETAILS
    supervisor_client.jobs.get_job.return_value = TEST_JOB_NOT_DONE

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "idle",
    }
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {"type": "backup/restore", "agent_id": "hassio.local", "backup_id": "abc123"}
    )
    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "restore_backup",
        "reason": None,
        "stage": None,
        "state": "in_progress",
    }

    supervisor_client.backups.partial_restore.assert_called_once_with(
        "abc123",
        supervisor_backups.PartialRestoreOptions(
            addons=None,
            background=True,
            folders=None,
            homeassistant=True,
            location=LOCATION_LOCAL_STORAGE,
            password=None,
        ),
    )

    supervisor_event_base = {"uuid": TEST_JOB_ID, "reference": "test_slug"}
    supervisor_events = [
        supervisor_event_base | {"done": False, "stage": "addon_repositories"},
        supervisor_event_base | {"done": False, "stage": None},  # Will be skipped
        supervisor_event_base | {"done": False, "stage": "unknown"},  # Will be skipped
        supervisor_event_base | {"done": False, "stage": "home_assistant"},
        supervisor_event_base | {"done": True, "stage": "addons"},
    ]
    expected_manager_events = [
        "addon_repositories",
        "home_assistant",
        "addons",
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
            "manager_state": "restore_backup",
            "reason": None,
            "stage": expected_manager_events[i],
            "state": "in_progress",
        }

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