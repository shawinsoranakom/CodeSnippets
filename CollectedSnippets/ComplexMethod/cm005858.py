async def test_update_provider_data_mixed_operations_preserve_encounter_order(monkeypatch):
    service = WatsonxOrchestrateDeploymentService(DummySettingsService())
    fake_agent = FakeAgentClient({"id": "dep-1", "tools": ["tool-1", "tool-2"]})
    fake_tool = FakeToolClient(
        [
            {
                "id": "tool-1",
                "name": "tool-1",
                "binding": {"langflow": {"connections": {"cfg-1": "conn-old-1", "cfg-2": "conn-old-2"}}},
            },
            {"id": "tool-2", "name": "tool-2", "binding": {"langflow": {"connections": {}}}},
            {"id": "tool-3", "name": "tool-3", "binding": {"langflow": {"connections": {}}}},
        ]
    )
    fake_clients = SimpleNamespace(
        agent=fake_agent,
        tool=fake_tool,
        connections=FakeConnectionsClient(existing_app_id="cfg-1"),
    )
    validate_calls: list[str] = []

    async def mock_get_provider_clients(*, user_id, db):  # noqa: ARG001
        return fake_clients

    async def mock_validate_connection(connections_client, *, app_id):  # noqa: ARG001
        validate_calls.append(app_id)
        return SimpleNamespace(connection_id=f"conn-{app_id}")

    monkeypatch.setattr(service, "_get_provider_clients", mock_get_provider_clients)
    monkeypatch.setattr(update_core_module, "validate_connection", mock_validate_connection)

    result = await service.update(
        user_id="user-1",
        deployment_id="dep-1",
        payload=DeploymentUpdate(
            provider_data={
                "tools": {},
                "connections": {},
                "llm": TEST_WXO_LLM,
                "operations": [
                    {"op": "bind", "tool": {"tool_id_with_ref": _tool_ref("tool-3")}, "app_ids": ["cfg-2", "cfg-1"]},
                    {"op": "unbind", "tool": _tool_ref("tool-1"), "app_ids": ["cfg-1", "cfg-2"]},
                    {"op": "remove_tool", "tool": _tool_ref("tool-2")},
                ],
            }
        ),
        db=object(),
    )

    assert validate_calls == ["cfg-2", "cfg-1"]
    assert result.provider_result is not None
    assert result.provider_result.created_app_ids == []
    assert result.provider_result.created_snapshot_ids == []
    assert result.provider_result.added_snapshot_ids == ["tool-3"]

    # Existing tool updates are dispatched concurrently via asyncio.gather, so
    # completion order is non-deterministic.  Assert the set of updated tool ids
    # and look up each payload by tool_id.
    update_calls_by_id = dict(fake_tool.update_calls)
    assert set(update_calls_by_id) == {"tool-3", "tool-1"}

    tool3_payload = update_calls_by_id["tool-3"]
    assert list(tool3_payload["binding"]["langflow"]["connections"]) == ["cfg-2", "cfg-1"]
    assert tool3_payload["binding"]["langflow"]["connections"] == {"cfg-2": "conn-cfg-2", "cfg-1": "conn-cfg-1"}

    tool1_payload = update_calls_by_id["tool-1"]
    assert tool1_payload["binding"]["langflow"]["connections"] == {}

    _, agent_payload = fake_agent.update_calls[0]
    assert agent_payload["tools"] == ["tool-1", "tool-3"]
    assert agent_payload["llm"] == TEST_WXO_LLM