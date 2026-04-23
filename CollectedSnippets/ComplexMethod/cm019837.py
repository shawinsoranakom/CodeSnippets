async def test_config_schedule_logic(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    create_backup: AsyncMock,
    commands: list[dict[str, Any]],
    last_completed_automatic_backup: str,
    time_1: str,
    time_2: str,
    attempted_backup_time: str,
    completed_backup_time: str,
    scheduled_backup_time: str,
    additional_backup: bool,
    backup_calls_1: int,
    backup_calls_2: int,
    call_args: Any,
    create_backup_side_effect: list[Exception | None] | None,
) -> None:
    """Test config schedule logic."""
    created_backup: MagicMock = create_backup.return_value[1].result().backup
    created_backup.protected = True

    client = await hass_ws_client(hass)
    storage_data = {
        "backups": [],
        "config": {
            "agents": {},
            "automatic_backups_configured": False,
            "create_backup": {
                "agent_ids": ["test.test-agent"],
                "include_addons": [],
                "include_all_addons": False,
                "include_database": True,
                "include_folders": [],
                "name": "test-name",
                "password": "test-password",
            },
            "retention": {"copies": None, "days": None},
            "last_attempted_automatic_backup": last_completed_automatic_backup,
            "last_completed_automatic_backup": last_completed_automatic_backup,
            "schedule": {
                "days": [],
                "recurrence": "daily",
                "time": None,
            },
        },
    }
    hass_storage[DOMAIN] = {
        "data": storage_data,
        "key": DOMAIN,
        "version": store.STORAGE_VERSION,
        "minor_version": store.STORAGE_VERSION_MINOR,
    }
    create_backup.side_effect = create_backup_side_effect
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to("2024-11-11 12:00:00+01:00")

    await setup_backup_integration(hass, remote_agents=["test.test-agent"])
    await hass.async_block_till_done()

    for command in commands:
        await client.send_json_auto_id(command)
        result = await client.receive_json()
        assert result["success"]

    await client.send_json_auto_id({"type": "backup/info"})
    result = await client.receive_json()
    assert result["result"]["next_automatic_backup"] == scheduled_backup_time
    assert result["result"]["next_automatic_backup_additional"] == additional_backup

    freezer.move_to(time_1)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert create_backup.call_count == backup_calls_1
    assert create_backup.call_args == call_args
    async_fire_time_changed(hass, fire_all=True)  # flush out storage save
    await hass.async_block_till_done()
    assert (
        hass_storage[DOMAIN]["data"]["config"]["last_attempted_automatic_backup"]
        == attempted_backup_time
    )
    assert (
        hass_storage[DOMAIN]["data"]["config"]["last_completed_automatic_backup"]
        == completed_backup_time
    )

    freezer.move_to(time_2)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert create_backup.call_count == backup_calls_2
    assert create_backup.call_args == call_args