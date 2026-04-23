async def test_configured_agents_unavailable_repair(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    issue_registry: ir.IssueRegistry,
    hass_storage: dict[str, Any],
) -> None:
    """Test creating and deleting repair issue for configured unavailable agents."""
    issue_id = "automatic_backup_agents_unavailable_test.agent"
    ws_client = await hass_ws_client(hass)
    hass_storage.update(
        {
            "backup": {
                "data": {
                    "backups": [],
                    "config": {
                        "agents": {},
                        "automatic_backups_configured": True,
                        "create_backup": {
                            "agent_ids": ["test.agent"],
                            "include_addons": None,
                            "include_all_addons": False,
                            "include_database": False,
                            "include_folders": None,
                            "name": None,
                            "password": None,
                        },
                        "retention": {"copies": None, "days": None},
                        "last_attempted_automatic_backup": None,
                        "last_completed_automatic_backup": None,
                        "schedule": {
                            "days": ["mon"],
                            "recurrence": "custom_days",
                            "time": None,
                        },
                    },
                },
                "key": DOMAIN,
                "version": store.STORAGE_VERSION,
                "minor_version": store.STORAGE_VERSION_MINOR,
            },
        }
    )

    await setup_backup_integration(hass)
    get_agents_mock = AsyncMock(return_value=[mock_backup_agent("agent")])
    register_listener_mock = Mock()
    await setup_backup_platform(
        hass,
        domain="test",
        platform=Mock(
            async_get_backup_agents=get_agents_mock,
            async_register_backup_agents_listener=register_listener_mock,
        ),
    )
    await hass.async_block_till_done()

    reload_backup_agents = register_listener_mock.call_args[1]["listener"]

    await ws_client.send_json_auto_id({"type": "backup/agents/info"})
    resp = await ws_client.receive_json()
    assert resp["result"]["agents"] == [
        {"agent_id": "backup.local", "name": "local"},
        {"agent_id": "test.agent", "name": "agent"},
    ]

    assert not issue_registry.async_get_issue(domain=DOMAIN, issue_id=issue_id)

    # Reload the agents with no agents returned.

    get_agents_mock.return_value = []
    reload_backup_agents()
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id({"type": "backup/agents/info"})
    resp = await ws_client.receive_json()
    assert resp["result"]["agents"] == [
        {"agent_id": "backup.local", "name": "local"},
    ]

    assert issue_registry.async_get_issue(domain=DOMAIN, issue_id=issue_id)

    await ws_client.send_json_auto_id({"type": "backup/config/info"})
    result = await ws_client.receive_json()
    assert result["result"]["config"]["create_backup"]["agent_ids"] == ["test.agent"]

    # Update the automatic backup configuration removing the unavailable agent.

    await ws_client.send_json_auto_id(
        {
            "type": "backup/config/update",
            "create_backup": {"agent_ids": ["backup.local"]},
        }
    )
    result = await ws_client.receive_json()

    assert not issue_registry.async_get_issue(domain=DOMAIN, issue_id=issue_id)

    await ws_client.send_json_auto_id({"type": "backup/config/info"})
    result = await ws_client.receive_json()
    assert result["result"]["config"]["create_backup"]["agent_ids"] == ["backup.local"]

    # Reload the agents with one agent returned
    # but not configured for automatic backups.

    get_agents_mock.return_value = [mock_backup_agent("agent")]
    reload_backup_agents()
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id({"type": "backup/agents/info"})
    resp = await ws_client.receive_json()
    assert resp["result"]["agents"] == [
        {"agent_id": "backup.local", "name": "local"},
        {"agent_id": "test.agent", "name": "agent"},
    ]

    assert not issue_registry.async_get_issue(domain=DOMAIN, issue_id=issue_id)

    await ws_client.send_json_auto_id({"type": "backup/config/info"})
    result = await ws_client.receive_json()
    assert result["result"]["config"]["create_backup"]["agent_ids"] == ["backup.local"]

    # Update the automatic backup configuration and configure the test agent.

    await ws_client.send_json_auto_id(
        {
            "type": "backup/config/update",
            "create_backup": {"agent_ids": ["backup.local", "test.agent"]},
        }
    )
    result = await ws_client.receive_json()

    assert not issue_registry.async_get_issue(domain=DOMAIN, issue_id=issue_id)

    await ws_client.send_json_auto_id({"type": "backup/config/info"})
    result = await ws_client.receive_json()
    assert result["result"]["config"]["create_backup"]["agent_ids"] == [
        "backup.local",
        "test.agent",
    ]

    # Reload the agents with no agents returned again.

    get_agents_mock.return_value = []
    reload_backup_agents()
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id({"type": "backup/agents/info"})
    resp = await ws_client.receive_json()
    assert resp["result"]["agents"] == [
        {"agent_id": "backup.local", "name": "local"},
    ]

    assert issue_registry.async_get_issue(domain=DOMAIN, issue_id=issue_id)

    await ws_client.send_json_auto_id({"type": "backup/config/info"})
    result = await ws_client.receive_json()
    assert result["result"]["config"]["create_backup"]["agent_ids"] == [
        "backup.local",
        "test.agent",
    ]

    # Update the automatic backup configuration removing all agents.

    await ws_client.send_json_auto_id(
        {
            "type": "backup/config/update",
            "create_backup": {"agent_ids": []},
        }
    )
    result = await ws_client.receive_json()

    assert not issue_registry.async_get_issue(domain=DOMAIN, issue_id=issue_id)

    await ws_client.send_json_auto_id({"type": "backup/config/info"})
    result = await ws_client.receive_json()
    assert result["result"]["config"]["create_backup"]["agent_ids"] == []