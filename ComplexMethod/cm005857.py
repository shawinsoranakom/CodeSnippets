async def test_update_provider_data_creates_raw_connection_and_raw_tool(monkeypatch):
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

    async def mock_create_config(*, clients, config, user_id, db):  # noqa: ARG001
        captured["created_app_id"] = config.name
        fake_connections._connections_by_app_id[config.name] = f"conn-{config.name}"
        return config.name

    async def mock_validate_connection(connections_client, *, app_id):  # noqa: ARG001
        return SimpleNamespace(connection_id=f"conn-{app_id}")

    async def mock_create_and_upload(*, clients, tool_bindings):
        _ = clients
        first_binding = tool_bindings[0]
        captured["connections"] = first_binding.connections
        return ["new-tool-1"]

    monkeypatch.setattr(service, "_get_provider_clients", mock_get_provider_clients)
    monkeypatch.setattr(shared_core_module, "create_config", mock_create_config)
    monkeypatch.setattr(update_core_module, "validate_connection", mock_validate_connection)
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
                "tools": {
                    "raw_payloads": [
                        {
                            "id": str(UUID("00000000-0000-0000-0000-000000000011")),
                            "name": "snapshot-new-1",
                            "description": "desc",
                            "data": {"nodes": [], "edges": []},
                            "tags": [],
                            "provider_data": {"project_id": "project-1", "source_ref": "fv-update-1"},
                        }
                    ]
                },
                "connections": {
                    "raw_payloads": [
                        {
                            "app_id": "cfg",
                            "environment_variables": {"API_KEY": {"source": "raw", "value": "secret"}},
                        }
                    ]
                },
                "llm": TEST_WXO_LLM,
                "operations": [
                    {
                        "op": "bind",
                        "tool": {"name_of_raw": "snapshot-new-1"},
                        "app_ids": ["cfg"],
                    }
                ],
            }
        ),
        db=object(),
    )

    assert captured["created_app_id"] == "cfg"
    assert captured["connections"] == {"cfg": "conn-cfg"}
    assert result.provider_result is not None
    assert result.provider_result.created_app_ids == ["cfg"]
    assert result.provider_result.created_snapshot_ids == ["new-tool-1"]
    assert result.provider_result.added_snapshot_ids == ["new-tool-1"]
    _, agent_payload = fake_agent.update_calls[0]
    assert agent_payload["tools"] == ["tool-1", "new-tool-1"]
    assert agent_payload["llm"] == TEST_WXO_LLM