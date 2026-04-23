async def test_restore_progress_after_restart_report_progress(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
) -> None:
    """Test restore backup progress after restart."""

    supervisor_client.jobs.get_job.return_value = TEST_JOB_NOT_DONE

    with patch.dict(os.environ, MOCK_ENVIRON | {RESTORE_JOB_ID_ENV: TEST_JOB_ID}):
        assert await async_setup_component(hass, BACKUP_DOMAIN, {BACKUP_DOMAIN: {}})

    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {
        "manager_state": "restore_backup",
        "reason": None,
        "stage": None,
        "state": "in_progress",
    }
    response = await client.receive_json()
    assert response["success"]

    supervisor_event_base = {"uuid": TEST_JOB_ID, "reference": "test_slug"}
    supervisor_events = [
        supervisor_event_base | {"done": False, "stage": "addon_repositories"},
        supervisor_event_base | {"done": False, "stage": None},  # Will be skipped
        supervisor_event_base | {"done": False, "stage": "unknown"},  # Will be skipped
        supervisor_event_base | {"done": False, "stage": "home_assistant"},
        supervisor_event_base | {"done": True, "stage": "addons"},
    ]
    expected_manager_events = ["addon_repositories", "home_assistant", "addons"]
    expected_manager_states = ["in_progress", "in_progress", "completed"]

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
            "state": expected_manager_states[i],
        }

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}

    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    assert response["success"]
    assert response["result"]["last_action_event"] == {
        "manager_state": "restore_backup",
        "reason": None,
        "stage": "addons",
        "state": "completed",
    }
    assert response["result"]["state"] == "idle"