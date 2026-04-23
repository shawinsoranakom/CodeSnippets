async def test_update_provider_data_creates_raw_tools_without_operations(monkeypatch):
    service = WatsonxOrchestrateDeploymentService(DummySettingsService())
    fake_agent = FakeAgentClient({"id": "dep-1", "tools": ["tool-1"]})
    fake_tool = FakeToolClient([{"id": "tool-1", "name": "tool-1", "binding": {"langflow": {"connections": {}}}}])
    fake_connections = FakeConnectionsClient()
    fake_clients = SimpleNamespace(
        agent=fake_agent,
        tool=fake_tool,
        connections=fake_connections,
    )
    captured: dict[str, object] = {}

    async def mock_get_provider_clients(*, user_id, db):  # noqa: ARG001
        return fake_clients

    async def mock_create_and_upload(*, clients, tool_bindings):
        _ = clients
        captured["tool_bindings"] = tool_bindings
        return ["new-tool-raw-1"]

    monkeypatch.setattr(service, "_get_provider_clients", mock_get_provider_clients)
    monkeypatch.setattr(
        update_core_module,
        "create_and_upload_wxo_flow_tools_with_bindings",
        mock_create_and_upload,
    )

    result = await service.update(
        user_id="user-1",
        deployment_id="dep-1",
        payload=DeploymentUpdate(
            provider_data={
                "llm": TEST_WXO_LLM,
                "tools": {
                    "raw_payloads": [
                        {
                            "id": str(UUID("00000000-0000-0000-0000-000000000071")),
                            "name": "snapshot-new-raw-only",
                            "description": "desc",
                            "data": {"nodes": [], "edges": []},
                            "tags": [],
                            "provider_data": {"project_id": "project-1", "source_ref": "fv-raw-only-1"},
                        }
                    ]
                },
            }
        ),
        db=object(),
    )

    assert captured["tool_bindings"][0].connections == {}
    assert result.provider_result is not None
    assert result.provider_result.created_snapshot_ids == ["new-tool-raw-1"]
    assert result.provider_result.added_snapshot_ids == ["new-tool-raw-1"]
    assert fake_connections.create_calls == []
    _, agent_payload = fake_agent.update_calls[0]
    assert agent_payload["tools"] == ["tool-1", "new-tool-raw-1"]
    assert agent_payload["llm"] == TEST_WXO_LLM