async def test_config_retention_copies_logic(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    create_backup: AsyncMock,
    get_backups: AsyncMock,
    command: dict[str, Any],
    backups: dict[str, Any],
    get_backups_agent_errors: dict[str, Exception],
    delete_backup_side_effects: dict[str, Exception],
    last_backup_time: str,
    next_time: str,
    backup_time: str,
    backup_calls: int,
    get_backups_calls: int,
    delete_calls: dict[str, Any],
) -> None:
    """Test config backup retention copies logic."""
    created_backup: MagicMock = create_backup.return_value[1].result().backup
    created_backup.protected = True

    client = await hass_ws_client(hass)
    storage_data = {
        "backups": [],
        "config": {
            "agents": {},
            "automatic_backups_configured": False,
            "create_backup": {
                "agent_ids": ["test-agent"],
                "include_addons": ["test-addon"],
                "include_all_addons": False,
                "include_database": True,
                "include_folders": ["media"],
                "name": "test-name",
                "password": "test-password",
            },
            "retention": {"copies": None, "days": None},
            "last_attempted_automatic_backup": None,
            "last_completed_automatic_backup": last_backup_time,
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
    get_backups.return_value = (backups, get_backups_agent_errors)
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to("2024-11-11 12:00:00+01:00")

    mock_agents = await setup_backup_integration(
        hass, remote_agents=["test.test-agent", "test.test-agent2"]
    )
    await hass.async_block_till_done()

    for agent_id, agent in mock_agents.items():
        agent.async_delete_backup.side_effect = delete_backup_side_effects.get(agent_id)

    await client.send_json_auto_id(command)
    result = await client.receive_json()

    assert result["success"]

    freezer.move_to(next_time)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert create_backup.call_count == backup_calls
    assert get_backups.call_count == get_backups_calls
    for agent_id, agent in mock_agents.items():
        agent_delete_calls = delete_calls.get(agent_id, [])
        assert agent.async_delete_backup.call_count == len(agent_delete_calls)
        assert agent.async_delete_backup.call_args_list == agent_delete_calls
    async_fire_time_changed(hass, fire_all=True)  # flush out storage save
    await hass.async_block_till_done()
    assert (
        hass_storage[DOMAIN]["data"]["config"]["last_attempted_automatic_backup"]
        == backup_time
    )
    assert (
        hass_storage[DOMAIN]["data"]["config"]["last_completed_automatic_backup"]
        == backup_time
    )