async def test_update_provider_data_binds_existing_tool_and_updates_agent_tools(monkeypatch):
    service = WatsonxOrchestrateDeploymentService(DummySettingsService())
    fake_agent = FakeAgentClient({"id": "dep-1", "tools": ["tool-1"]})
    fake_tool = FakeToolClient(
        [
            {"id": "tool-1", "name": "tool-1", "binding": {"langflow": {"connections": {}}}},
            {"id": "tool-3", "name": "tool-3", "binding": {"langflow": {"connections": {}}}},
        ]
    )
    fake_clients = SimpleNamespace(
        agent=fake_agent,
        tool=fake_tool,
        connections=FakeConnectionsClient(existing_app_id="cfg-new"),
    )

    async def mock_get_provider_clients(*, user_id, db):  # noqa: ARG001
        return fake_clients

    async def mock_validate_connection(connections_client, *, app_id):  # noqa: ARG001
        assert app_id == "cfg-new"
        return SimpleNamespace(connection_id="conn-new")

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
                    {
                        "op": "bind",
                        "tool": {"tool_id_with_ref": _tool_ref("tool-3")},
                        "app_ids": ["cfg-new"],
                    }
                ],
            }
        ),
        db=object(),
    )

    assert result.provider_result is not None
    assert result.provider_result.created_app_ids == []
    assert result.provider_result.created_snapshot_ids == []
    assert result.provider_result.added_snapshot_ids == ["tool-3"]
    assert [tool_id for tool_id, _payload in fake_tool.update_calls] == ["tool-3"]
    _, updated_tool_payload = fake_tool.update_calls[0]
    assert updated_tool_payload["binding"]["langflow"]["connections"]["cfg-new"] == "conn-new"
    _, agent_payload = fake_agent.update_calls[0]
    assert agent_payload["tools"] == ["tool-1", "tool-3"]
    assert agent_payload["llm"] == TEST_WXO_LLM