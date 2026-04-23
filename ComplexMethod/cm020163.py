async def test_reader_writer_create_per_agent_encryption(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    supervisor_client: AsyncMock,
    commands: list[dict[str, Any]],
    password: str | None,
    agent_ids: list[str],
    password_sent_to_supervisor: str | None,
    create_locations: list[str],
    create_protected: bool,
    upload_locations: list[str | None],
) -> None:
    """Test generating a backup."""
    client = await hass_ws_client(hass)
    freezer.move_to("2025-01-30 13:42:12.345678")
    mounts = MountsInfo(
        default_backup_mount=None,
        mounts=[
            supervisor_mounts.CIFSMountResponse(
                share=f"share{i}",
                name=f"share{i}",
                read_only=False,
                state=supervisor_mounts.MountState.ACTIVE,
                user_path=PurePath(f"share{i}"),
                usage=supervisor_mounts.MountUsage.BACKUP,
                server=f"share{i}",
                type=supervisor_mounts.MountType.CIFS,
            )
            for i in range(4)
        ],
    )
    supervisor_client.backups.partial_backup.return_value.job_id = UUID(TEST_JOB_ID)
    supervisor_client.backups.backup_info.return_value = replace(
        TEST_BACKUP_DETAILS,
        extra=DEFAULT_BACKUP_OPTIONS.extra,
        location_attributes={
            location: supervisor_backups.BackupLocationAttributes(
                protected=create_protected,
                size_bytes=1048576,
            )
            for location in create_locations
        },
    )
    supervisor_client.jobs.get_job.return_value = TEST_JOB_NOT_DONE
    supervisor_client.mounts.info.return_value = mounts
    assert await async_setup_component(hass, BACKUP_DOMAIN, {BACKUP_DOMAIN: {}})

    for command in commands:
        await client.send_json_auto_id(command)
        result = await client.receive_json()
        assert result["success"] is True

    await client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
    response = await client.receive_json()
    assert response["success"]

    await client.send_json_auto_id(
        {
            "type": "backup/generate",
            "agent_ids": agent_ids,
            "name": "Test",
            "password": password,
        }
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
        replace(
            DEFAULT_BACKUP_OPTIONS,
            password=password_sent_to_supervisor,
            location=create_locations,
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

    assert len(supervisor_client.backups.upload_backup.mock_calls) == len(
        upload_locations
    )
    for call in supervisor_client.backups.upload_backup.mock_calls:
        assert call.args[1].filename == PurePath("Test_2025-01-30_05.42_12345678.tar")
        upload_call_locations: set = call.args[1].location
        assert len(upload_call_locations) == 1
        assert upload_call_locations.pop() in upload_locations
    supervisor_client.backups.remove_backup.assert_not_called()

    response = await client.receive_json()
    assert response["event"] == {"manager_state": "idle"}