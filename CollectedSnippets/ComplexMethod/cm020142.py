async def test_mount_refresh_after_issue(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    supervisor_client: AsyncMock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test hassio mount state is refreshed after an issue was send by the supervisor."""
    # Add a mount.
    mock_mounts: list[CIFSMountResponse | NFSMountResponse] = [
        CIFSMountResponse(
            share="files",
            server="1.2.3.4",
            name="NAS",
            type=MountType.CIFS,
            usage=MountUsage.SHARE,
            read_only=False,
            state=MountState.ACTIVE,
            user_path=PurePath("/share/nas"),
        )
    ]
    supervisor_client.mounts.info = AsyncMock(
        return_value=MountsInfo(default_backup_mount=None, mounts=mock_mounts)
    )

    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        assert result
    await hass.async_block_till_done()

    # Enable the entity.
    entity_id = "binary_sensor.nas_connected"
    entity_registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Test new entity.
    entity = hass.states.get(entity_id)
    assert entity is not None
    assert entity.state == "on"

    # Change mount state to failed, issue a repair, and verify entity's state.
    mock_mounts[0] = replace(mock_mounts[0], state=MountState.FAILED)
    client = await hass_ws_client(hass)
    issue_uuid = uuid4().hex
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "mount_failed",
                    "context": "mount",
                    "reference": "nas",
                    "suggestions": [
                        {
                            "uuid": uuid4().hex,
                            "type": "execute_reload",
                            "context": "mount",
                            "reference": "nas",
                        },
                        {
                            "uuid": uuid4().hex,
                            "type": "execute_remove",
                            "context": "mount",
                            "reference": "nas",
                        },
                    ],
                },
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done(wait_background_tasks=True)
    entity = hass.states.get(entity_id)
    assert entity is not None
    assert entity.state == "off"

    # Change mount state to active, issue a repair, and verify entity's state.
    mock_mounts[0] = replace(mock_mounts[0], state=MountState.ACTIVE)
    await client.send_json(
        {
            "id": 2,
            "type": "supervisor/event",
            "data": {
                "event": "issue_removed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "mount_failed",
                    "context": "mount",
                    "reference": "nas",
                },
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done(wait_background_tasks=True)
    entity = hass.states.get(entity_id)
    assert entity is not None
    assert entity.state == "on"